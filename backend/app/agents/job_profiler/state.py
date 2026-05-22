from typing import TypedDict, Dict


class JobProfilerState(TypedDict, total=False):
    job_info: dict           # INPUT: 岗位基本信息
    job_requirements: dict   # OUTPUT: 7维度能力要求画像
