import logging
from datetime import datetime
import requests
from typing import List
import concurrent.futures
import json

# 日志配置
logging.basicConfig(
    level=logging.INFO,  # 日志级别为INFO
    format="%(asctime)s - %(levelname)s - %(message)s",  # 日志格式
    filename="reservation.log",  # 日志文件名
    filemode="a",  # 追加模式
)


class Result:
    def __init__(self, code=0, message="操作成功", data=None):
        self.code = code  # 业务状态码 0-成功 1-失败
        self.message = message  # 提示信息
        self.data = data  # 响应数据

    @staticmethod
    def success(data=None):
        return Result(0, "操作成功", data)

    @staticmethod
    def error(message):
        return Result(1, message, None)

    def finalData(self):
        return {"code": self.code, "message": self.message, "data": self.data}


class SportsFacilityReservation:
    session_cache = {}
    field_cache = {}

    def __init__(self, config) -> None:
        self.proxies = {"http": "", "https": ""}
        self.headers = {
            "width": "414",
            "os-version": "Windows 11 x64",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090b19)XWEB/11253",
            "height": "736",
            "xweb_xhr": "1",
            "X-UserToken": config["personToken"],
            "device-name": "microsoft",
            "os": "windows",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://servicewechat.com/wx34c9f462afa158b3/23/page-frame.html",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "token": config["personToken"],
        }
        self.reserveDate = datetime.strptime(
            config["reserveDate"], "%Y-%m-%d"
        ).strftime("%Y-%m-%d")
        self.reservePlace = config["reservePlace"]
        self.reserveList = config["reserveList"]

    @staticmethod
    def getLibraryInfo(headers, proxies, reserveDate, reservePlace) -> Result:
        if reservePlace in SportsFacilityReservation.session_cache:
            logging.info(f"使用缓存的场地信息: {reservePlace}")
            return Result.success(SportsFacilityReservation.session_cache[reservePlace])

        try:
            if reservePlace not in SportsFacilityReservation.field_cache:
                place_url = "https://zhcg.swjtu.edu.cn/onesports-gateway/wechat-c/api/wechat/memberBookController/fields?sportTypeId=2"
                response = requests.get(url=place_url, headers=headers, proxies=proxies)
                fieldId = {
                    "九里": response.json()["fieldList"][0]["id"],
                    "犀浦": response.json()["fieldList"][1]["id"],
                }
                SportsFacilityReservation.field_cache = fieldId
                logging.info(f"场地缓存已更新: {fieldId}")
            weChatSessionsListUrl = "https://zhcg.swjtu.edu.cn/onesports-gateway/wechat-c/api/wechat/memberBookController/weChatSessionsList"
            reserveData = {
                "fieldId": SportsFacilityReservation.field_cache[reservePlace],
                "isIndoor": "",
                "placeTypeId": "",
                "searchDate": reserveDate,
                "sportTypeId": "2",
            }
            response = requests.post(
                url=weChatSessionsListUrl,
                json=reserveData,
                headers=headers,
                proxies=proxies,
            )
            response.raise_for_status()

            if "msg" in response.json() and "code" in response.json():
                logging.error(f"获取场地信息失败: {response.json().get('msg')}")
                return Result.error(response.json().get("msg"))

            logging.info(f"获取场地信息成功: {reservePlace}")
            return Result.success({reservePlace: response.json()})

        except requests.RequestException as e:
            logging.error(f"请求失败: {str(e)}")
            return Result.error(f"请求失败: {str(e)}")

    def reserveField(self) -> List[Result]:
        fieldResult = SportsFacilityReservation.getLibraryInfo(
            self.headers, self.proxies, self.reserveDate, self.reservePlace
        ).finalData()

        if fieldResult["code"] != 0:
            logging.error(f"获取场地信息失败: {fieldResult['message']}")
            return [Result.error(fieldResult["message"])]

        sessionList = fieldResult["data"][self.reservePlace]
        requestsLists = [
            {"sessionsId": sessionList[col][row]["id"]} for row, col in self.reserveList
        ]
        reserveUrl = "https://zhcg.swjtu.edu.cn/onesports-gateway/business-service/orders/weChatSessionsReserve"
        orderUseDate = int(
            datetime.strptime(self.reserveDate, "%Y-%m-%d").timestamp() * 1000
        )

        reserveResults = []

        def send_request(requestsList, reservePlaceId):
            reserveData = {
                "number": reservePlaceId,
                "orderUseDate": orderUseDate,
                "requestsList": requestsList,
                "fieldName": f"{self.reservePlace}羽毛球馆",
                "fieldId": SportsFacilityReservation.field_cache[self.reservePlace],
                "siteName": f"{reservePlaceId}号羽毛球",
                "sportTypeName": "羽毛球",
                "sportTypeId": "2",
            }

            try:
                response = requests.post(
                    url=reserveUrl,
                    json=reserveData,
                    headers=self.headers,
                    proxies=self.proxies,
                ).json()
                if response["code"] != 200:
                    logging.error(f"预约失败: {response['msg']}")
                    return Result.error(response["msg"])
                logging.info(f"预约成功，订单ID: {response['orderId']}")
                return Result.success({"orderId": response["orderId"]})

            except requests.RequestException as e:
                logging.error(f"预约请求失败: {str(e)}")
                return Result.error(f"预约请求失败: {str(e)}")

        # 使用多线程并行发送请求
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    send_request, [requestsLists[i]], self.reserveList[i][1] + 1
                )
                for i in range(len(requestsLists))
            ]
            for future in concurrent.futures.as_completed(futures):
                reserveResults.append(future.result())

        return reserveResults


def load_config(filename="config.json"):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    config = load_config()
    reservation = SportsFacilityReservation(config)
    reserveResults = reservation.reserveField()
    for reserveResult in reserveResults:
        message = reserveResult.finalData()["message"]
        logging.info(f"预约结果: {message}")
        print(message)


if __name__ == "__main__":
    while True:
        main()
