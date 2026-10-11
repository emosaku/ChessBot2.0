# ChessBot2.0 — Cloud Implementation

As of 2026-10-09 · Online version: https://claude.ai/code/artifact/25febc9a-bfe1-4945-bb6b-308d2f847896

## Architecture

The engine runs as a container on one Spot VM, with the 3–5 and 6-piece Syzygy tables on an attached disk. For positions with 7 pieces or fewer, it asks the Lichess tablebase API for the move at the root. The opening book is built offline by a Cloud Run job and copied to the Mac.

**Tablebase coverage, decided 2026-10-09:** the 3–5 and 6-piece tables (150.1 GiB) on the VM's disk serve the search, and the Lichess tablebase API covers 7-piece positions at the root. Self-hosting the 7-piece set (8.5 TiB WDL only, 16.7 TiB in full, roughly $950–1,900/month in disk) is ruled out.

```
Your Mac                              GCP project (us-west1)                         External
--------                              ----------------------                         --------
pygame app (--engine-url) --IAP tunnel :8080--> VM chess-engine (c4d-highcpu-8 Spot)
   | on timeout                                    Engine service: FastAPI POST /move --> Lichess tablebase API
   v                                               (book, tablebase, then search)          (7 pieces, root only)
Local engine (fallback)                               | WDL / DTZ probes
                                                      v
                                                   Hyperdisk syzygy: 200 GB, read-only, 3-4-5 + 6-piece
Opening book (lichess.bin) <-- gsutil cp --        Cloud Storage (pgn/, books/)     Artifact Registry --> VM (pulls image)
                                                      ^ book
                                                   Cloud Run job build-book  <-- monthly PGN -- Lichess DB
```

The pygame app reaches the service through an IAP tunnel on port 8080. If the service doesn't answer in time, the local engine plays the move. The arrows show requests and data copies; the book file reaches the Mac with one `gsutil cp`.

## Components and costs

The standing cost is the 200 GB tablebase disk. Everything else is either billed per hour of play or a one-off. The region is us-west1 to match Fantasydashboard.

| Resource | Spec | Purpose | Approx. cost |
| --- | --- | --- | --- |
| Compute Engine VM `chess-engine` | `c4d-highcpu-8` Spot, Debian 12, no public IP | Runs the engine service container | Per running hour only; stopped between sessions |
| Hyperdisk Balanced `syzygy` | 200 GB, baseline 3,000 IOPS / 140 MiB/s | 3–5 and 6-piece WDL + DTZ files (150.1 GiB) | Roughly $15–25/month (estimate) |
| Boot disk | 20 GB Hyperdisk Balanced | OS + Docker | ~$2/month (estimate) |
| Artifact Registry `chessbot` | Docker repo | Engine image | < $1/month |
| Cloud Storage `gs://<project>-chessbot` | Standard class | Source PGNs, built opening book | < $1/month |
| Cloud Run job `build-book` | 4 vCPU / 8 GiB per task | Builds the opening book (Option B) | A few dollars per build (estimate) |
| Lichess tablebase API | `tablebase.lichess.ovh` | 7-piece lookups at the root | Free |

C4D VMs accept only Hyperdisk volumes, not Persistent Disk ([docs](https://docs.cloud.google.com/compute/docs/general-purpose-machines)). Hyperdisk Balanced includes 3,000 IOPS and 140 MiB/s at no extra charge ([docs](https://docs.cloud.google.com/compute/docs/disks/hd-types/hyperdisk-balanced)), which is enough for one engine probing WDL files. Confirm every price in the [pricing calculator](https://cloud.google.com/products/calculator) before creating anything, and set a billing budget alert at $50/month.

## Engine service

The engine becomes a small FastAPI service that takes a position and a time budget and returns one move. The pygame app stays on your Mac and calls it. If the service doesn't answer, the app falls back to the local engine.

### API

```http
POST /move
{"fen": "8/8/4k3/8/3KP3/8/8/8 w - - 0 1", "time_ms": 3000}

200 OK
{"move": "d4e3", "source": "tablebase-local", "wdl": 2, "dtz": 13,
 "depth": null, "nodes": 0, "ms": 4}
```

- `source` is one of `book`, `tablebase-local`, `tablebase-lichess` or `search`. The sidebar can show where each move came from.
- `GET /healthz` returns the largest tablebase piece count loaded and the number of book entries. The client calls it at startup to decide between remote and local play.

### How each move is chosen

1. **Book:** look up the position in the Option B opening book (see below). A hit returns at once.
2. **7 pieces or fewer, no castling rights:** call `GET https://tablebase.lichess.ovh/standard?fen=…` with a 1.5 s timeout. Play the first move in its sorted `moves` list, and cache the answer by FEN.
3. **6 pieces or fewer, no castling rights, Lichess unavailable:** probe local DTZ for every legal move and rank them:
   1. best WDL first;
   2. among winning moves, keep only those with `dtz + halfmove_clock ≤ 100`, then prefer a capture or pawn move, then the smallest |DTZ|;
   3. among losing moves, take the largest |DTZ|.
4. **Otherwise:** iterative-deepening alpha-beta for `time_ms`. Inside the search, probe local WDL at any node with 6 pieces or fewer, no castling rights and `halfmove_clock == 0`.
   - Map WDL ±2 to ±(20000 − ply), below the mate score of 99999.
   - Map ±1 (cursed win or blessed loss) to ±1 centipawn, which is effectively a draw.

### Code to add

| File | Contents |
| --- | --- |
| `engine/tablebase.py` | `Tablebase` wrapper: `open_tablebase` over each directory under `/syzygy`, `max_pieces`, `wdl(board)` using `get_wdl` (returns None, never raises), `best_root_move(board)`, and the Lichess client with its cache |
| `engine/minimax.py` | WDL probe in the search, root DTZ / Lichess step before the search, iterative deepening on a time budget |
| `service/app.py` | FastAPI app: `/move`, `/healthz`; loads the book and tablebases once at startup |
| `service/Dockerfile` | `python:3.12-slim`, installs `chess`, `fastapi`, `uvicorn`, `httpx`; runs `uvicorn service.app:app --host 0.0.0.0 --port 8080` |
| `ui/remote_engine.py` | `RemoteEngine(BaseEngine)`: posts the FEN, times out after `time_ms + 2 s`, then falls back to the local `AlphaBetaEngine` |
| `main.py` | `--engine-url` flag; with no flag, the app is fully local as today |

## Step-by-step setup

Setup is a one-time job of about an hour, plus the time to download the 150 GiB of tables. The VM has no public IP; your Mac reaches it through an Identity-Aware Proxy (IAP) tunnel, so no port is open to the internet.

1. **Project and variables**

```bash
export PROJECT=<your-project> REGION=us-west1 ZONE=us-west1-b
gcloud config set project $PROJECT
gcloud services enable compute.googleapis.com artifactregistry.googleapis.com \
  cloudbuild.googleapis.com run.googleapis.com iap.googleapis.com
```

2. **Tablebase disk and VM**

```bash
gcloud compute disks create syzygy --zone=$ZONE \
  --type=hyperdisk-balanced --size=200GB

gcloud compute instances create chess-engine --zone=$ZONE \
  --machine-type=c4d-highcpu-8 --provisioning-model=SPOT \
  --instance-termination-action=STOP --no-address \
  --image-family=debian-12 --image-project=debian-cloud \
  --boot-disk-type=hyperdisk-balanced --boot-disk-size=20GB \
  --disk=name=syzygy,device-name=syzygy,mode=rw

gcloud compute firewall-rules create allow-iap --direction=INGRESS \
  --source-ranges=35.235.240.0/20 --allow=tcp:22,tcp:8080
```

3. **Format, mount and fill the disk** (on the VM: `gcloud compute ssh chess-engine --zone=$ZONE --tunnel-through-iap`). The VM has no public IP, so it needs Cloud NAT for outbound downloads: `gcloud compute routers create nat-router --network=default --region=$REGION` and then `gcloud compute routers nats create nat --router=nat-router --region=$REGION --auto-allocate-nat-external-ips --nat-all-subnet-ip-ranges`.

```bash
sudo mkfs.ext4 -m 0 /dev/disk/by-id/google-syzygy
sudo mkdir -p /mnt/syzygy
echo '/dev/disk/by-id/google-syzygy /mnt/syzygy ext4 defaults,nofail 0 2' | sudo tee -a /etc/fstab
sudo mount /mnt/syzygy && cd /mnt/syzygy
for d in 3-4-5-wdl 3-4-5-dtz 6-wdl 6-dtz; do
  sudo wget -q -r -np -nH --cut-dirs=3 -R 'index.html*' \
    https://tablebase.lichess.ovh/tables/standard/$d/
done
du -sh /mnt/syzygy/*   # expect about 0.9 GiB for the 3-4-5 sets and 149 GiB for the 6-piece sets
```

Then remount read-only (change `defaults` to `ro,defaults` in `/etc/fstab`) so the engine can never write to the tables. Spot-check one known 6-piece win with `chess.syzygy` before relying on them.

4. **Install Docker, build and push the image**

```bash
# on the VM
sudo apt-get update && sudo apt-get install -y docker.io
sudo gcloud auth configure-docker $REGION-docker.pkg.dev

# on your Mac, from ChessBot2.0/
gcloud artifacts repositories create chessbot --repository-format=docker --location=$REGION
gcloud builds submit --config=service/cloudbuild.yaml .   # one docker build step using service/Dockerfile, tagged $REGION-docker.pkg.dev/$PROJECT/chessbot/engine:latest
gcloud artifacts repositories add-iam-policy-binding chessbot --location=$REGION \
  --member=serviceAccount:$(gcloud compute instances describe chess-engine --zone=$ZONE --format='value(serviceAccounts[0].email)') \
  --role=roles/artifactregistry.reader
```

5. **Run the service** (on the VM)

```bash
sudo docker run -d --name engine --restart=always -p 8080:8080 \
  -v /mnt/syzygy:/syzygy:ro \
  $REGION-docker.pkg.dev/$PROJECT/chessbot/engine:latest
```

6. **Play from your Mac**

```bash
gcloud compute start-iap-tunnel chess-engine 8080 --local-host-port=localhost:8080 --zone=$ZONE &
curl localhost:8080/healthz          # {"tablebase_max_pieces": 6, "book_entries": ...}
python main.py --engine-url http://localhost:8080
```

## Opening book build (Option B)

The opening book is built from Lichess games by a Cloud Run job, and the result is a single Polyglot file in Cloud Storage. The engine service and the local app both load that file, so book moves are always instant and need no network.

**Source:** the [Lichess open database](https://database.lichess.org/) (CC0, monthly `.pgn.zst` files). Start with the 3 most recent months, copied into `gs://<project>-chessbot/pgn/`.

**Filters and parameters** (all flags of `tools/build_book.py`):

| Parameter | Value | Why |
| --- | --- | --- |
| `--min-elo` | 2200 for both players | Moves a strong player would choose |
| `--time-controls` | rapid, classical, and blitz of 3+2 or longer | Fewer hurried opening mistakes |
| `--max-plies` | 24 (12 moves each) | Book covers the opening, the search takes over after |
| `--min-games` | 30 per move | Drops one-off moves |
| `--min-score` | 0.45 for the side to move | Drops moves that lose more than they win |
| weight | (wins + draws / 2) × games, scaled to 0–65535 | Popular and successful moves are picked most |

**How the job runs:**

1. **Map:** one task per month file (`CLOUD_RUN_TASK_INDEX` picks the file). It streams the file with `zstandard` and `chess.pgn`, applies the filters, and writes counts keyed by (Zobrist hash, move) to `gs://…/counts/<month>.json.gz`.
2. **Reduce:** one task merges the counts, applies `--min-games` and `--min-score`, and writes `gs://…/books/lichess.bin`, sorted by key.

```bash
gcloud run jobs deploy build-book --region=$REGION \
  --image=$REGION-docker.pkg.dev/$PROJECT/chessbot/engine:latest \
  --command=python --args=tools/build_book.py,map \
  --tasks=3 --cpu=4 --memory=8Gi --task-timeout=6h
gcloud run jobs execute build-book --region=$REGION --wait
# then the reduce step, as a second job or as the same job with --args=tools/build_book.py,reduce --tasks=1
gsutil cp gs://$PROJECT-chessbot/books/lichess.bin assets/books/
```

Polyglot entry format: `struct.pack(">QHHI", key, move, weight, 0)`. The move is packed as `to_file | to_rank<<3 | from_file<<6 | from_rank<<9 | promo<<12`, with promo 1 to 4 for knight to queen. Castling is stored as the king taking its own rook (`e1h1`); python-chess's reader converts it back.

**`OpeningBook` changes:** the default path becomes `assets/books/lichess.bin`, with `8moves_v3.bin` as the fallback. Add a `mode` setting, `weighted` (today's behaviour, gives variety) or `best` (top weight), and a `max_moves` cut-off, 12 by default.

## Operations

The VM runs only while you play. Start it before a session, and stop it after; the disk and the book stay.

```bash
gcloud compute instances start chess-engine --zone=$ZONE   # container restarts on its own
gcloud compute instances stop  chess-engine --zone=$ZONE
```

**Cost control**

- An instance schedule stops the VM every night at 02:00 in case you forget: `gcloud compute resource-policies create instance-schedule nightly-stop --region=$REGION --vm-stop-schedule='0 2 * * *' --timezone=America/Los_Angeles`, then `gcloud compute instances add-resource-policies chess-engine --resource-policies=nightly-stop --zone=$ZONE`.
- A billing budget at $50/month with alerts at 50%, 90% and 100%.
- Delete the `pgn/` and `counts/` folders in Cloud Storage after each book build; keep only `books/`.

**What happens when something fails**

| Failure | Behaviour |
| --- | --- |
| Spot VM pre-empted mid-game | The client's request times out after `time_ms + 2 s` and the local engine plays the move. Restart the VM with `instances start`. |
| Lichess tablebase API slow or down | 1.5 s timeout, then local 6-piece DTZ. With 7 pieces and no local table, the search plays on. |
| A table file missing or corrupt | `get_wdl` returns None, so that position is searched normally. `/healthz` reports the piece count actually loaded. |
| Book file missing | `OpeningBook` falls back to `8moves_v3.bin`, then to search. |

**Open questions**

- Is C4D available in us-west1-b? If not, use another us-west1 zone or us-central1, keeping the disk and VM in the same zone.
- Lichess publishes no rate limit for the tablebase API. One call per engine move with a cache should be well within fair use; say so in a `User-Agent` header with a contact address.
- Is a 6-piece WDL probe inside the search worth its disk reads at this engine's speed? Measure nodes per second with and without it once the search is faster.
- The engine image also runs the book job, so it needs `zstandard` and `tools/` included. Alternatively, build a separate small `book-builder` image.
