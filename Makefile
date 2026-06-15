.PHONY: up down build logs ps backend test eval reindex

# 全栈启动
up:
	docker compose up -d

# 停止所有服务
down:
	docker compose down

# 重新构建镜像
build:
	docker compose build

# 查看日志
logs:
	docker compose logs -f

# 查看服务状态
ps:
	docker compose ps

# 仅启动后端（开发模式，不依赖 Docker 基础设施时）
backend:
	python main.py

test:
	pytest

eval:
	python eval/retrieval_eval.py

eval-ragas:
	python eval/ragas_eval.py

eval-ragas-quick:
	python eval/ragas_eval.py --limit 5

reindex:
	python scripts/reindex_collection.py
