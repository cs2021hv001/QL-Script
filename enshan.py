import json
import os
import re

import requests
import urllib3

# 假设 dailycheckin 和 CheckIn 在您的项目结构中是可用的
# 如果不在，您可能需要调整导入或提供该类的定义
# from dailycheckin import CheckIn

# 由于没有 dailycheckin.py 的内容，我将创建一个占位符类以便脚本可以独立运行
class CheckIn:
    def __init__(self, check_item):
        self.check_item = check_item
    def main(self):
        raise NotImplementedError

urllib3.disable_warnings()


class EnShan(CheckIn):
    name = "恩山无线论坛"

    def __init__(self, check_item):
        self.check_item = check_item

    @staticmethod
    def sign(cookie):
        msg = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.125 Safari/537.36",
            "Cookie": cookie,
        }
        # 增加超时和异常处理
        try:
            response = requests.get(
                url="https://www.right.com.cn/FORUM/home.php?mod=spacecp&ac=credit&showcredit=1",
                headers=headers,
                verify=False,
                timeout=15  # 增加超时设置
            )
            response.raise_for_status() # 如果请求失败则抛出异常
        except requests.exceptions.RequestException as e:
            msg = [{"name": "请求失败", "value": str(e)}]
            return msg
        
        # 使用更稳健的正则匹配
        try:
            coin_match = re.search("恩山币: </em>(.*?)&nbsp;", response.text)
            point_match = re.search("<em>积分: </em>(.*?)<span", response.text)

            if coin_match and point_match:
                coin = coin_match.group(1)
                point = point_match.group(1)
                msg = [
                    {
                        "name": "恩山币",
                        "value": coin,
                    },
                    {
                        "name": "积分",
                        "value": point,
                    },
                ]
            else:
                 msg = [{"name": "签到失败", "value": "无法在页面上找到恩山币或积分信息"}]
        except Exception as e:
            msg = [
                {
                    "name": "解析失败",
                    "value": str(e),
                }
            ]
        return msg

    def main(self):
        cookie = self.check_item.get("cookie")
        if not cookie:
            return "错误: cookie 未提供。"
        msg = self.sign(cookie=cookie)
        msg = "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])
        return msg


if __name__ == "__main__":
    # 从环境变量获取 cookie
    ENSHANCK = os.getenv("ENSHANCK")

    if not ENSHANCK:
        print("错误: 环境变量 'ENSHANCK' 未设置。")
        print("请先设置该环境变量后再运行脚本。")
    else:
        # 将 cookie 封装成 check_item 字典
        _check_item = {"cookie": ENSHANCK}
        # 实例化并运行主程序
        result = EnShan(check_item=_check_item).main()
        print(result)
