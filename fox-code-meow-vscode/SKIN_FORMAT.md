# 自定义动作图

右键桌宠可导入两种格式：
1. PNG图集：6行，1–30列。行依次为idle待机、wave走路、happy开心、pat摸头、sleep睡觉、think思考。自己保证每格完整角色与透明留白，导入只按网格切分，不自动抠图或补全截断肢体。
2. 文件夹：skin.json与透明PNG。manifest示例：

```json
{"name":"my-fox","fps":8,"states":{"idle":["idle-0.png","idle-1.png"],"wave":["walk-0.png","walk-1.png"]}}
```

idle必须存在，其他组缺失时使用idle。各组1–60帧，帧路径必须在目录内，最大边长2048、整体解码像素2400万、文件合计80MB。导入后复制到本机skin目录。右键恢复默认狐狸娘不删除你的原图。
