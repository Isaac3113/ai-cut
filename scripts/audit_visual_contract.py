"""Plan synchronized presenter inserts or audit actual frozen evidence. Read-only."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from talking_head_editor.visual_contract import audit_contract, plan_presenter, retime_speech


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['audit','plan-pip','retime'])
    parser.add_argument('input', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--expected-speed',type=float,default=1.2)
    parser.add_argument('--start-frame',type=int,default=0)
    args=parser.parse_args()
    if args.out.exists():
        parser.error('Output exists; preserve evidence and choose a new path')
    raw=args.input.read_bytes()
    data=json.loads(raw.decode('utf-8-sig'))
    if args.action=='audit':
        result=audit_contract(data,args.expected_speed)
    elif args.action=='plan-pip':
        result={'pip_segments':plan_presenter(data['speech_segments'],data['full_screen_visuals'],data['fps']),
                'status':'proposal_only; apply through the real editor and inspect actual bounds/mask'}
    else:
        result={'speech_segments':retime_speech(data['speech_segments'],args.expected_speed,data['fps'],args.start_frame),
                'status':'proposal_only; refresh the single authoritative timeline and all dependent layers'}
    result['input_sha256']=hashlib.sha256(raw).hexdigest()
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result.get('ready_for_brand_delivery',True) else 1


if __name__=='__main__':
    raise SystemExit(main())
