import sys
import os
import subprocess
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from _0_infra.util import get_merge_root


local_dir = os.path.join(get_merge_root(), '_0_data', '_0_raw')
hdfs_dir = '/project-root/data/_0_raw'

# 업로드 실행
for filename in os.listdir(local_dir):
    local_path = os.path.join(local_dir, filename)
    subprocess.run(["hdfs", "dfs", "-put", "-f", local_path, hdfs_dir], check=True)

print("✅ HDFS 업로드 완료!")