# Emby注册服务部署指南（粗野主义UI版本）

## 项目说明

这是基于 [guowanghushifu/emby-register-service](https://github.com/guowanghushifu/emby-register-service) 的二次开发版本，主要改进：

- ✅ 采用粗野主义（Brutalism）设计风格的UI界面
- ✅ 高饱和度配色方案（亮黄色 #FFD700 + 洋红色 #FF1493）
- ✅ 粗线条、大圆角、强对比的视觉设计
- ✅ 无依赖外部CDN，所有样式内联
- ✅ 保留原有完整功能

## 部署步骤

### 方式一：Fork到自己的GitHub仓库

1. **Fork原仓库**
   - 访问您当前的GitHub账号
   - 点击右上角 "Fork" 按钮
   - 创建自己的仓库副本

2. **配置GitHub Secrets（用于自动构建推送到DockerHub）**

   进入您Fork的仓库 → Settings → Secrets and variables → Actions → New repository secret

   需要添加以下两个secrets：
   - `DOCKERHUB_USERNAME`: 您的DockerHub用户名
   - `DOCKERHUB_TOKEN`: 您的DockerHub访问令牌

   获取DockerHub Token：
   - 登录 https://hub.docker.com
   - 点击右上角头像 → Account Settings → Security
   - 点击 "New Access Token"
   - 创建一个新的访问令牌并复制

3. **修改GitHub Actions配置**

   编辑 `.github/workflows/build-docker-image.yml` 文件：

   ```yaml
   # 修改第37行，将镜像名称改为您的DockerHub用户名
   images: unclesamo/emby-register-brutalist
   ```

4. **推送代码触发构建**

   ```bash
   git add .
   git commit -m "Configure Docker build for my account"
   git push origin main
   ```

   GitHub Actions 会自动构建并推送到您的DockerHub仓库。

### 方式二：本地构建Docker镜像

```bash
# 克隆仓库
git clone <your-repo-url>
cd emby-register

# 构建镜像
docker build -t unclesamo/emby-register-brutalist:latest .

# 推送到DockerHub
docker login
docker push unclesamo/emby-register-brutalist:latest
```

## 运行Docker容器

### 使用docker run

```bash
docker run -d \
  --name emby-register \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -e FLASK_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')" \
  -e ADMIN_PASSWORD="your_admin_password" \
  -e EMBY_SERVER_URL="http://your-emby-server:8096" \
  -e EMBY_API_KEY="your_emby_api_key" \
  -e COPY_FROM_USER_ID="template_user_id" \
  -e PUBLIC_ACCESS_URL="https://your-domain.com" \
  unclesamo/emby-register-brutalist:latest
```

### 使用docker-compose

创建 `docker-compose.yml` 文件：

```yaml
version: '3.8'

services:
  emby-register:
    image: unclesamo/emby-register-brutalist:latest
    container_name: emby-register
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
    environment:
      - FLASK_SECRET_KEY=your_flask_secret_key_here
      - ADMIN_PASSWORD=your_admin_password
      - EMBY_SERVER_URL=http://your-emby-server:8096
      - EMBY_API_KEY=your_emby_api_key
      - COPY_FROM_USER_ID=template_user_id
      - PUBLIC_ACCESS_URL=https://your-domain.com
    restart: unless-stopped
```

启动服务：

```bash
docker-compose up -d
```

## 环境变量说明

| 变量名 | 必需 | 说明 |
|--------|------|------|
| FLASK_SECRET_KEY | ✅ | Flask密钥，用于session加密 |
| ADMIN_PASSWORD | ✅ | 管理员登录密码 |
| EMBY_SERVER_URL | ✅ | Emby服务器地址 |
| EMBY_API_KEY | ✅ | Emby API密钥 |
| COPY_FROM_USER_ID | ✅ | 模板用户ID（新用户会复制此用户的权限设置） |
| PUBLIC_ACCESS_URL | ✅ | 公网访问地址（用于生成注册链接） |

## 使用说明

1. **管理员登录**
   - 访问 `http://your-domain:5000/login`
   - 输入管理员密码

2. **生成注册Token**
   - 登录后台，点击"生成新TOKEN"
   - 复制生成的注册链接分享给用户

3. **用户注册**
   - 用户访问注册链接
   - 填写用户名和密码
   - 完成注册

## UI设计特点

### 粗野主义风格特征

- **配色方案**：高饱和度亮黄色（#FFD700）+ 洋红色（#FF1493）
- **边框**：4-5px黑色粗边框
- **阴影**：6-8px偏移，无模糊的硬阴影
- **圆角**：16-20px的夸张圆角
- **字体**：900字重的无衬线字体，紧凑行距
- **按钮**：按下时有视觉位移效果
- **表格**：黑色表头，黄色高亮行

### 设计原则

- 功能优先，信息密度高
- 用色块和粗边框划分区域
- 避免渐变，保持色块纯粹性
- 强烈的视觉冲击和工业感

## 常见问题

**Q: 如何获取COPY_FROM_USER_ID？**

A: 登录Emby后台 → 用户 → 选择模板用户 → URL中的ID即为用户ID

**Q: 如何修改UI颜色？**

A: 编辑 `templates/layout.html` 中的CSS变量：
- 主色调黄色：`#FFD700`
- 强调色洋红：`#FF1493`
- 成功色绿色：`#00FF00`
- 信息色蓝色：`#00BFFF`

**Q: GitHub Actions构建失败？**

A: 检查：
1. DOCKERHUB_USERNAME 和 DOCKERHUB_TOKEN secrets是否正确配置
2. DockerHub Token是否有写入权限
3. workflow文件中的镜像名称是否正确

## 许可证

基于原项目的开源许可证。

## 致谢

- 原项目：[guowanghushifu/emby-register-service](https://github.com/guowanghushifu/emby-register-service)
- UI设计风格：Brutalism (Neo-Brutalism) Web Design
