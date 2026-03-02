# ls2file

Dump a recursive file listing with timestamps to a TSV file.

## Usage

```bash
uv run ls2file /media/vega/ThinThicc /home/vega/Documents/thinthicc_drive_backup.tsv --progress
```

## Options

- `--no-dirs` exclude directories from output
- `--exclude-hidden` skip hidden files/dirs
- `--progress` show a progress bar with ETA (extra count pass)
- `--progress-interval N` update progress every N entries
