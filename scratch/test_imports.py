import sys
import os

print("PYTHONPATH:", sys.path)
print("Working dir:", os.getcwd())

try:
    from utils.data_loader import performance_label
    print("utils.data_loader performance_label imported successfully!")
except Exception as e:
    print("utils.data_loader performance_label failed:", e)

try:
    from utils.charts import GREEN
    print("utils.charts GREEN imported successfully!")
except Exception as e:
    print("utils.charts GREEN failed:", e)
