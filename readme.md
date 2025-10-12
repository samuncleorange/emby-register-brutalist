# Emby注册服务 - 粗野主义UI版本

> 本项目是基于 [guowanghushifu/emby-register-service](https://github.com/guowanghushifu/emby-register-service) 的二次开发版本

## 致谢原作者

**原项目**: [emby-register-service](https://github.com/guowanghushifu/emby-register-service)
**原作者**: [guowanghushifu](https://github.com/guowanghushifu)

感谢原作者 guowanghushifu 使用 Google Gemini 2.5 开发了这个实用的工具，方便分享emby服务给朋友注册。本项目在原项目基础上进行了UI重新设计。

---

## 本版本的改进

本分支主要改进了用户界面，采用粗野主义（Brutalism/Neo-Brutalism）设计风格：

✅ **全新UI设计**
- 高饱和度配色：亮黄色(#FFD700) + 洋红色(#FF1493)
- 4-5px黑色粗边框 + 硬阴影效果
- 16-24px夸张圆角
- 900字重粗体字
- 强烈的视觉冲击和工业感

✅ **技术优化**
- 移除Bootstrap依赖，所有样式内联
- 更快的加载速度
- 保留原有完整功能

✅ **Docker镜像**
- DockerHub: `unclesamo/emby-register-brutalist:latest`
- 支持多架构：linux/amd64, linux/arm64

---

## 原作者说明

### 这个工具是原作者使用Google Gemini 2.5写出来的，只是能用的水平，方便分享自己的emby服务给朋友去注册
### 使用方法
1. 使用本版本的Docker镜像： `unclesamo/emby-register-brutalist:latest` 或者进入代码目录自己构建： `docker build -t emby-register-brutalist .`
   - 原版镜像：`guowanghushifu/emby-register-service` （原作者版本）
2. 找台安装了python的机器执行 `python3 -c "import secrets; print(secrets.token_hex(32) + '\n')"` 生成签名的密钥填到 FLASK_SECRET_KEY 环境变量
3. 修改docker-compose.yml中的其他环境变量
- PUBLIC_ACCESS_URL: 你这个docker的公网访问地址，如果非标准端口，一起写上，例如 https://your-domain.com:18080
- ADMIN_PASSWORD：你的管理员密码，不要用弱密码
- EMBY_SERVER_URL：EMBY服务器的地址，如果非标准端口，一起写上，例如 https://emby.your-domain.com:8920
- EMBY_API_KEY：和EMBY服务器交互的时候需要用到的API，去emby服务器管理面板里面申请
- COPY_FROM_USER_ID：从模板用户复制emby参数，这里填写他的ID，看如下说明

先去emby里面创建一个模板用户，注意不要给他管理权限!!!，把这个用户的各项参数配置好，例如他是否能看所有的库，是否能转码，是否能删除文件等；然后在控制台用户管理那里点这个用户，浏览器地址栏会显示这样的一串（举例）：https://emby.your-domain.com:8920/web/index.html#!/users/user?userId=a22935174ac24711aa54f84999999⁠ ，把userId= 这后面的这串代码a22935174ac24711aa54f84999999拷贝出来，写到 COPY_FROM_USR_ID 这个环境变量

4. 浏览器访问 PUBLIC_ACCESS_URL 填写管理员密码就可以创建token，分发给需要注册的用户了

### docker-compose.yml 示例

**本版本（粗野主义UI）**:
```yaml
services:
    emby-register-service:
        ports:
            - 18080:5000
        volumes:
            - ./data:/app/data
        container_name: my-emby-register-app
        environment:
            - FLASK_SECRET_KEY=54a7a4e7d286d13dbf610f14677d11290dede4eb8f0f20f01f3b57b109530f8d
            - PUBLIC_ACCESS_URL=https://your-reg-domain.com
            - ADMIN_PASSWORD=your_admin_password
            - EMBY_SERVER_URL=https://emby.your-domain.com:8920
            - EMBY_API_KEY=your_api_key
            - COPY_FROM_USER_ID=your_template_user_id
        restart: unless-stopped
        image: unclesamo/emby-register-brutalist:latest
```

**原版**:
```yaml
services:
    emby-register-service:
        image: guowanghushifu/emby-register-service
        # ... 其他配置相同
```

### Token管理界面

**原版界面**:
![PixPin_2025-06-08_16-24-41.png](https://image.dooo.ng/c/2025/06/08/68454b033e0d3.webp)

### 用户注册界面

**原版界面**:
![PixPin_2025-06-08_16-25-49.png](https://image.dooo.ng/c/2025/06/08/68454b02d33ec.webp)

**本版本界面**: 采用粗野主义设计风格，具有强烈的视觉冲击力和工业感。

---

## 详细部署文档

查看 [DEPLOY.md](DEPLOY.md) 了解完整的部署说明和配置指南。

## 相关链接

- **原项目**: https://github.com/guowanghushifu/emby-register-service
- **本项目**: https://github.com/samuncleorange/emby-register-brutalist
- **DockerHub**: https://hub.docker.com/r/unclesamo/emby-register-brutalist
- **原作者DockerHub**: https://hub.docker.com/r/guowanghushifu/emby-register-service

## 许可证

本项目基于原项目的开源许可证，遵守原作者的授权条款。

## 贡献

欢迎提交Issue和Pull Request！

如果您喜欢原项目，请访问 [原项目仓库](https://github.com/guowanghushifu/emby-register-service) 给原作者一个Star ⭐
