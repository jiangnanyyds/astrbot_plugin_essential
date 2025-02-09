import aiohttp
import urllib.parse
from astrbot.api.all import AstrMessageEvent, CommandResult, Context, Image, Plain, Video

class Main:
    def __init__(self, context: Context) -> None:
        self.PLUGIN_NAME = "astrbot_plugin_essential"
        # 注册“搜番”命令
        context.register_commands(self.PLUGIN_NAME, "搜番", "以图搜番", 1, self.get_search_anime)

    def time_convert(self, t):
        m, s = divmod(t, 60)
        return f"{int(m)}分{int(s)}秒"

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
            return CommandResult().error("格式：/搜番 [图片]")

        try:
            # 对图片 URL 进行编码，并添加到请求参数中
            params["url"] = urllib.parse.quote(image_obj.url, safe='')
            # 拼接完整请求 URL
            query = "&".join([f"{k}={v}" if v != "" else k for k, v in params.items()])
            url = f"{base_url}?{query}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return CommandResult().error(f"请求失败，状态码：{resp.status}")
                    data = await resp.json()

            # 若返回中有 error 字段，则直接返回错误信息
            if "error" in data and data["error"]:
                return CommandResult().error(data["error"])

            if data.get("result") and len(data["result"]) > 0:
                chain_list = []
                # 遍历所有匹配结果
                for res in data["result"]:
                    # 将秒数转换为分秒格式
                    res["from"] = self.time_convert(res["from"])
                    res["to"] = self.time_convert(res["to"])
                    warn = ""
                    if float(res["similarity"]) < 0.8:
                        warn = "相似度较低，可能不是同一番剧。\n"
                    # 拼接文本信息
                    text = (
                        f"{warn}番名: {res['anilist']['title']['native']}\n"
                        f"相似度: {res['similarity']}\n"
                        f"剧集: 第{res.get('episode', '未知')}集\n"
                        f"时间: {res['from']} - {res['to']}\n"
                        "精准空降截图:"
                    )
                    chain_list.append(Plain(text))
                    chain_list.append(Image.fromURL(res["image"]))
                    # 如果有视频预览，则加入媒体预览消息
                    if "video" in res and res["video"]:
                        chain_list.append(Plain("媒体预览:"))
                        chain_list.append(Video.fromURL(res["video"]))
                return CommandResult(chain=chain_list, use_t2i_=False)
            else:
                return CommandResult().error("没有找到番剧")
        except Exception as e:
            return CommandResult().error(f"发生异常：{e}")
