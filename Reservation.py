from datetime import datetime
import requests
from typing import List


# 统一全局返回结果
class Result:
    def __init__(self, code=0, message="操作成功", data=None):
        self.code = code  # 业务状态码  0-成功  1-失败
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


class Reservation:
    def __init__(self, personToken, reserveDate, reservePlace, reserveList) -> None:
        self.proxies = {"http": "", "https": ""}
        self.headers = {
            "width": "414",
            "os-version": "Windows 11 x64",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090b19)XWEB/11253",
            "height": "736",
            "xweb_xhr": "1",
            "X-UserToken": personToken,
            "device-name": "microsoft",
            "os": "windows",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://servicewechat.com/wx34c9f462afa158b3/23/page-frame.html",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "token": personToken,
        }
        self.reserveDate = datetime.strptime(reserveDate, "%Y-%m-%d").strftime(
            "%Y-%m-%d"
        )
        self.reservePlace = reservePlace
        self.reserveList = reserveList
        self.fieldId = {
            "九里": "",
            "犀浦": "",
        }

    # 获取场馆信息
    @staticmethod
    def getLibraryInfo(headers, proxies, reserveDate, reservePlace, fieldId) -> Result:
        place_url = "https://zhcg.swjtu.edu.cn/onesports-gateway/wechat-c/api/wechat/memberBookController/fields?sportTypeId=2"
        response = requests.get(url=place_url, headers=headers, proxies=proxies)
        fieldId["九里"] = response.json()["fieldList"][0]["id"]
        fieldId["犀浦"] = response.json()["fieldList"][1]["id"]
        # 通过场馆ID获取具体场地信息
        weChatSessionsListUrl = "https://zhcg.swjtu.edu.cn/onesports-gateway/wechat-c/api/wechat/memberBookController/weChatSessionsList"
        reserveData = {
            "fieldId": fieldId[reservePlace],
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
        # 获取失败，返回错误信息
        if (
            response.status_code == 200
            and "msg" in response.json()
            and "code" in response.json()
        ):
            return Result.error(response.json().get("msg"))
        # 获取成功，返回场地信息
        return Result.success(response.json())

    # 预约场地
    def reserveField(self) -> List[Result]:
        fieldResult = Reservation.getLibraryInfo(
            self.headers,
            self.proxies,
            self.reserveDate,
            self.reservePlace,
            self.fieldId,
        ).finalData()
        if fieldResult["code"] != 0:
            return Result.error(fieldResult["message"])
        sessionList = fieldResult["data"]
        requestsLists = []
        for row, col in self.reserveList:
            reservePlaceId = col + 1
            requestsLists.append({"sessionsId": sessionList[col][row]["id"]})
        reserveUrl = "https://zhcg.swjtu.edu.cn/onesports-gateway/business-service/orders/weChatSessionsReserve"
        orderUseDate = int(
            datetime.strptime(self.reserveDate, "%Y-%m-%d").timestamp() * 1000
        )
        reserveResults = []
        for i in range(len(requestsLists)):
            requestsList = []
            requestsList.append(requestsLists[i])
            reserveData = {
                "犀浦": {
                    "number": reservePlaceId,
                    "orderUseDate": orderUseDate,
                    "requestsList": requestsList,
                    "fieldName": "犀浦室内羽毛球馆",
                    "fieldId": self.fieldId["犀浦"],
                    "siteName": f"{reservePlaceId}号羽毛球",
                    "sportTypeName": "羽毛球",
                    "sportTypeId": "2",
                },
                "九里": {
                    "number": reservePlaceId,
                    "orderUseDate": orderUseDate,
                    "requestsList": requestsList,
                    "fieldName": "九里羽毛球1-6号",
                    "fieldId": self.fieldId["九里"],
                    "siteName": f"{reservePlaceId}号羽毛球",
                    "sportTypeName": "羽毛球",
                    "sportTypeId": "2",
                },
            }
            response = requests.post(
                url=reserveUrl,
                json=reserveData[self.reservePlace],
                headers=self.headers,
                proxies=self.proxies,
            ).json()
            if response["code"] != 200:
                reserveResults.append(Result.error(response["msg"]))
            else:
                reserveResults.append(Result.success({"orderId": response["orderId"]}))
        return reserveResults


def main():
    personToken = "token"
    reservePlace = "犀浦"
    reserveDate = "2024-09-18"
    reserveList = [
        (4, 2),
        (5, 2),
        (6, 2),
        (7, 2),
        (8, 2),
    ]
    reservation = Reservation(personToken, reserveDate, reservePlace, reserveList)
    reserveResults = reservation.reserveField()
    for reserveResult in reserveResults:
        print(reserveResult.finalData()["message"])


if __name__ == "__main__":
    main()
