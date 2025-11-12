# My SRE Portfolio
这是一个极简的 Flask 示例应用，用于展示基本的 Linux / Git / Docker 操作和本地部署流程。

## 先决条件
- 本地运行：需要安装 Python 3.11+（建议使用虚拟环境）
- 使用 Docker：只需安装 Docker；使用 Docker 时无需在宿主机安装 Python


## 本地运行（不使用 Docker）
1. 克隆仓库并进入目录：
```sh
git clone https://github.com/Peopyo/my-sre-portfolio.git
cd my-sre-portfolio
```
2. 建议：创建并激活虚拟环境：
```sh
python3 -m venv venv
# mac / linux
source venv/bin/activate
# windows (PowerShell)
venv\Scripts\Activate.ps1
```
3. 安装依赖并运行：
```sh
pip install flask
python3 app.py
```
4. 在浏览器打开：http://localhost:5000

## 使用 Docker 运行
1. 克隆仓库并进入目录：
```sh
git clone https://github.com/Peopyo/my-sre-portfolio.git
cd my-sre-portfolio
```
2. 构建镜像：
```sh
docker build -t my-sre-portfolio .
```
3. 运行容器并映射端口：
```sh
docker run -p 5000:5000 my-sre-portfolio
```
4. 在浏览器打开：http://localhost:5000

## 文件说明
- [app.py](app.py) — Flask 应用主文件，包含 Flask 实例 [`app`](app.py) 和路由函数 [`home`](app.py)
- [Dockerfile](Dockerfile) — 镜像构建说明，直接安装 Flask 并运行 `app.py`
- [.gitignore](.gitignore) — 忽略本地虚拟环境 `venv/`

## 其他说明
- 应用监听在 0.0.0.0:5000（参见 [`app.run`](app.py)）


