"""CLI for local offline document corpora."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from body_of_secrets.archive import Archive
from .offline_docs import ingest_directory, search_archive

def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(prog="body-of-secrets-offline-docs")
    parser.add_argument("--db",default="data/archive.db")
    sub=parser.add_subparsers(dest="command",required=True)
    ingest=sub.add_parser("ingest",help="Import a local text corpus into the canonical Archive")
    ingest.add_argument("directory",type=Path)
    ingest.add_argument("--source-prefix",default=None)
    ingest.add_argument("--max-file-bytes",type=int,default=25*1024*1024)
    search=sub.add_parser("search",help="Search the canonical Archive")
    search.add_argument("query")
    search.add_argument("--limit",type=int,default=8)
    sub.add_parser("mcp",help="Run local stdio MCP server")
    args=parser.parse_args(argv)
    if args.command=="mcp":
        from .offline_docs import mcp_server
        mcp_server()
        return 0
    with Archive(args.db) as archive:
        if args.command=="ingest":
            if args.max_file_bytes<=0: parser.error("--max-file-bytes must be positive")
            result=ingest_directory(archive,args.directory,args.source_prefix,args.max_file_bytes)
        else:
            result={"results":search_archive(archive,args.query,args.limit)}
        print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
