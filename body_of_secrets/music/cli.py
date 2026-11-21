"""Standalone symbolic music command-line interface."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from .encoder import encode_directory
from .snapshots import SnapshotStore
from .training import train_music

def main(argv=None):
    parser=argparse.ArgumentParser(prog="5-senses-music"); sub=parser.add_subparsers(dest="command",required=True)
    enc=sub.add_parser("encode"); enc.add_argument("source"); enc.add_argument("--output",default="music_data/corpus/symbolic_music.txt")
    tr=sub.add_parser("train"); tr.add_argument("source"); tr.add_argument("--work-dir",default="music_data")
    tr.add_argument("--order",type=int,default=5); tr.add_argument("--iterations",type=int,default=0)
    pred=sub.add_parser("predict"); pred.add_argument("--work-dir",default="music_data")
    pred.add_argument("--context",required=True); pred.add_argument("--limit",type=int,default=8)
    rb=sub.add_parser("rollback"); rb.add_argument("version"); rb.add_argument("--work-dir",default="music_data")
    args=parser.parse_args(argv)
    if args.command=="encode":
        records=encode_directory(args.source,args.output); print(json.dumps({"files":len(records),"output":args.output})); return 0
    if args.command=="train":
        print(train_music(args.source,work_dir=args.work_dir,order=args.order,max_iterations=args.iterations)); return 0
    store=SnapshotStore(Path(args.work_dir)/"snapshots")
    if args.command=="predict":
        model,_=store.load(); print(json.dumps(model.continuations(args.context,args.limit),indent=2)); return 0
    if args.command=="rollback":
        store.rollback(args.version,Path(args.work_dir)/"corpus"/"symbolic_music.txt")
        print("Restored "+args.version); return 0
    return 2

if __name__=="__main__": raise SystemExit(main())
