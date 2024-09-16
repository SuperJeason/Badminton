import requests
from datetime import datetime, timedelta, time


class Badminton:
    def __init__(self):
        self.proxies = {"http": "", "https": ""}
        self.headers = {
            "width": "414",
            "os-version": "Windows 11 x64",
            "height": "736",
            "Content-Type": "application/json",
            "xweb_xhr": "1",
            "X-UserToken": "579d348a-f156-4fac-8102-435f47833963",
            "device-name": "microsoft",
            "os": "windows",
            "token": "579d348a-f156-4fac-8102-435f47833963",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        # 获取当前日期并格式化为字符串
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        # 将日期字符串转换为 datetime 对象
        current_date_dt = datetime.strptime(current_date_str, "%Y-%m-%d")
        # 添加 2 天
        new_date_dt = current_date_dt + timedelta(days=2)
        # 将新日期转换为字符串
        new_date_str = new_date_dt.strftime("%Y-%m-%d")
        # self.current_time = new_date_str
        # 1.改时间
        self.current_time = datetime(2024, 9, 16).strftime("%Y-%m-%d")
        self.place = "犀浦"
        self.fieldId = {
            "九里": "",
            "犀浦": "",
        }
        self.sessionList = {
            "九里": [],
            "犀浦": [],
        }

    def get_placeeId(self):
        # 获取场地信息url
        place_url = "https://zhcg.swjtu.edu.cn/onesports-gateway/wechat-c/api/wechat/memberBookController/fields?sportTypeId=2"
        response = requests.get(
            url=place_url, headers=self.headers, proxies=self.proxies
        )
        self.fieldId["九里"] = response.json()["fieldList"][0]["id"]
        self.fieldId["犀浦"] = response.json()["fieldList"][1]["id"]
        print(self.fieldId)
        # 获取场次信息
        weChatSessionsListUrl = "https://zhcg.swjtu.edu.cn/onesports-gateway/wechat-c/api/wechat/memberBookController/weChatSessionsList"

        # 2.改信息
        data = {
            "fieldId": self.fieldId[self.place],
            "isIndoor": "",
            "placeTypeId": "",
            "searchDate": self.current_time,
            "sportTypeId": "2",
        }

        r = requests.post(
            url=weChatSessionsListUrl,
            json=data,
            headers=self.headers,
            proxies=self.proxies,
        )
        # 3.改信息
        # 储存1到9号场次信息
        self.sessionList[self.place] = r.json()

    def booking(self, selected_cells):
        bookUrl = "https://zhcg.swjtu.edu.cn/onesports-gateway/business-service/orders/weChatSessionsReserve"
        requestsList = []
        selected_col = 0
        self.get_placeeId()
        for row, col in selected_cells:
            selected_col = col + 1
            # 4.改信息
            requestsList.append(
                {"sessionsId": self.sessionList[self.place][col][row]["id"]}
            )
        orderUseDate = ""
        current_time_dt = datetime.strptime(self.current_time, "%Y-%m-%d")
        orderUseDate = int(current_time_dt.timestamp() * 1000)
        # 5.改信息
        data = {
            "犀浦": {
                "number": selected_col,
                "orderUseDate": orderUseDate,
                "requestsList": requestsList,
                "fieldName": "犀浦室内羽毛球馆",
                "fieldId": self.fieldId[self.place],
                "siteName": f"{selected_col}号羽毛球",
                "sportTypeName": "羽毛球",
                "sportTypeId": "2",
            },
            "九里": {
                "number": selected_col,
                "orderUseDate": orderUseDate,
                "requestsList": requestsList,
                "fieldName": "九里羽毛球1-6号",
                "fieldId": self.fieldId["九里"],
                "siteName": f"{selected_col}号羽毛球",
                "sportTypeName": "羽毛球",
                "sportTypeId": "2",
            },
        }
        response = requests.post(
            url=bookUrl,
            json=data[self.place],
            headers=self.headers,
            proxies=self.proxies,
        )
        print(response.json)


def main():
    badminton = Badminton()
    # 6.改时间
    selected_cells = [
        (4,2),
    ]
    badminton.booking(selected_cells)


if __name__ == "__main__":
    main()
