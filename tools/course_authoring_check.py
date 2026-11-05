"""Check coverage plan and validated reviewed-card library."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from content_registry import read_plan,load_reviewed_resources
plan=read_plan()
items=load_reviewed_resources()
print('目录:',len(plan['sections']),'节  |  候选原子知识点:',len(plan['atoms']))
print('完整资源规划:',sum(plan['targets'].values()),'张（初高中总计）')
print('通过质量门槛且明确审核的新增资源:',len(items),'张')
print('说明：现有265张短知识卡另存于旧系统；课程样板讲解不冒充已审核成品卡。')
