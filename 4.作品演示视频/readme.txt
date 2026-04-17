系统通过config.yaml统一管理后端端口（5008）、前端端口（3000）及百度地图AccessKey等核心配置。app.py启动时自动读取该配置，将VUE_APP_BACKEND_IP、VUE_APP_BACKEND_POR等环境变量写入 frontend1/.env 文件，使前端构建时自动获取正确的API地址，无需手工配置，实现“一键启动”：
（1）安装后端依赖
pip install -r requirements.txt
（2）配置数据库（修改 backend/.flaskenv）
MYSQL_HOST=127.0.0.1
MYSQL_PASSWORD=你的MySQL密码
（3）配置邮件（修改backend/.flaskenv）
MAIL_USERNAME=xxx@qq.com
MAIL_PASSWORD=QQ邮箱授权码
（4）启动后端（自动初始化数据库、写入前端.env）
python app.py
（5）启动前端
cd frontend1 && npm install && npm run serve
系统初次启动时，init_db.py 脚本会自动检测MySQL中是否存在目标数据库，若不存在则自动创建，并通过Flask-Migrate完成表结构迁移，减少了运维操作成本。


运行网址：http://localhost:3000