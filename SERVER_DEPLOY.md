# 服务器部署说明

## 配置摘要

- **服务地址**: https://reg.vim.im
- **管理员密码**: piggo.register
- **Emby服务器**: https://ee.vim.im
- **容器名称**: emby-register-brutalist
- **端口映射**: 5000:5000

## 部署步骤

### 1. 上传docker-compose.yml到服务器

```bash
# 在服务器上创建目录
mkdir -p ~/emby-register
cd ~/emby-register

# 上传docker-compose.yml文件到这个目录
# 可以使用scp、sftp或直接复制粘贴
```

### 2. 启动服务

```bash
cd ~/emby-register

# 拉取最新镜像
docker-compose pull

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 3. 验证服务

```bash
# 检查容器状态
docker-compose ps

# 应该看到类似输出：
# NAME                      IMAGE                                      STATUS
# emby-register-brutalist   unclesamo/emby-register-brutalist:latest   Up X minutes
```

### 4. 配置反向代理（Nginx示例）

如果您使用Nginx作为反向代理，配置示例：

```nginx
server {
    listen 443 ssl http2;
    server_name reg.vim.im;

    # SSL证书配置
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5. 访问服务

访问 https://reg.vim.im 并使用管理员密码 `piggo.register` 登录。

## 常用命令

```bash
# 查看日志
docker-compose logs -f

# 停止服务
docker-compose stop

# 启动服务
docker-compose start

# 重启服务
docker-compose restart

# 停止并删除容器
docker-compose down

# 更新镜像并重启
docker-compose pull && docker-compose up -d

# 进入容器
docker exec -it emby-register-brutalist sh
```

## 备份与恢复

### 备份数据库

```bash
# 备份data目录（包含tokens.db）
tar -czf emby-register-backup-$(date +%Y%m%d).tar.gz data/
```

### 恢复数据库

```bash
# 解压备份
tar -xzf emby-register-backup-YYYYMMDD.tar.gz

# 重启服务
docker-compose restart
```

## 故障排查

### 检查容器日志
```bash
docker-compose logs --tail=100
```

### 检查网络连接
```bash
# 从容器内测试Emby服务器连接
docker exec emby-register-brutalist wget -O- https://ee.vim.im
```

### 重新生成SECRET_KEY
如果需要重新生成Flask密钥：
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
# 然后更新docker-compose.yml中的FLASK_SECRET_KEY
```

## 安全建议

1. ✅ 定期备份data目录
2. ✅ 使用强管理员密码（已设置：piggo.register）
3. ✅ 启用HTTPS（配置SSL证书）
4. ✅ 定期更新镜像：`docker-compose pull && docker-compose up -d`
5. ✅ 监控日志，及时发现异常

## 环境变量说明

| 变量 | 值 | 说明 |
|------|-----|------|
| FLASK_SECRET_KEY | d8ea61b...09fb2f0dd | Flask会话加密密钥 |
| ADMIN_PASSWORD | piggo.register | 管理员登录密码 |
| EMBY_SERVER_URL | https://ee.vim.im | Emby服务器地址 |
| EMBY_API_KEY | b73252c0...171505c3b | Emby API密钥 |
| COPY_FROM_USER_ID | c2ea1659...757dcb618 | 模板用户ID |
| PUBLIC_ACCESS_URL | https://reg.vim.im | 公网访问地址 |
| MOVIEPILOT_URL | (可选) | Moviepilot 服务器地址 |
| MOVIEPILOT_USER | (可选) | Moviepilot 管理员用户名 |
| MOVIEPILOT_PASSWORD | (可选) | Moviepilot 管理员密码 |
