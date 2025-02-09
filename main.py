async def get_search_anime(self, message: AstrMessageEvent, context: Context):
    message_obj = message.message_obj
    # 构造请求 URL，添加 anilistInfo、cutBorders 参数以及 limit 限制
    base_url = "https://api.trace.moe/search"
    params = {
        "anilistInfo": "",
        "cutBorders": "",
        "limit": "10",
    }
    image_obj = None
    for part in message_obj.message:
        if isinstance(part, Image):
            image_obj = part
            break
    if not image_obj:
        yield CommandResult().error("格式：/搜番 [图片]")  # 使用 yield 代替 return

    try:
        # 对图片 URL 进行编码，并添加到请求参数中
        params["url"] = urllib.parse.quote(image_obj.url, safe='')
        # 拼接完整请求 URL
        query = "&".join([f"{k}={v}" if v != "" else k for k, v in params.items()])
        url = f"{base_url}?{query}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    yield CommandResult().error(f"请求失败，状态码：{resp.status}")
                data = await resp.json()

        # 若返回中有 error 字段，则直接返回错误信息
        if "error" in data and data["error"]:
            yield CommandResult().error(data["error"])

        if data.get("result") and len(data["result"]) > 0:
            # 发送文本描述
            for res in data["result"]:
                res["from"] = self.time_convert(res["from"])
                res["to"] = self.time_convert(res["to"])
                warn = ""
                if float(res["similarity"]) < 0.8:
                    warn = "相似度较低，可能不是同一番剧。\n"
                text = (
                    f"{warn}番名: {res['anilist']['title']['native']}\n"
                    f"相似度: {res['similarity']}\n"
                    f"剧集: 第{res.get('episode', '未知')}集\n"
                    f"时间: {res['from']} - {res['to']}\n"
                    "精准空降截图:"
                )
                yield Plain(text)
                yield Image.fromURL(res["image"])
                # 如果有视频预览，则发送视频消息
                if "video" in res and res["video"]:
                    yield Video.fromURL(res["video"])
            yield CommandResult().use_t2i(False)  # 使用 yield 代替 return
        else:
            yield CommandResult().error("没有找到番剧")
    except Exception as e:
        yield CommandResult().error(f"发生异常：{e}")
