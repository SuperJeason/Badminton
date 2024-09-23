import logging
from datetime import datetime, timedelta
import requests
from typing import List
import concurrent.futures
import json
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class Result:
    def __init__(self, code=0, message="操作成功", data=None):
        self.code = code
        self.message = message
        self.data = data

    @staticmethod
    def success(data=None):
        return Result(0, "操作成功", data).finalData()

    @staticmethod
    def error(message):
        return Result(1, message, None).finalData()

    def finalData(self):
        return {"code": self.code, "message": self.message, "data": self.data}


class SportsFacilityReservation:
    session_cache = {}
    field_cache = {}

    def __init__(self, config) -> None:
        self.proxies = {"http": "", "https": ""}
        self.headers = config["headers"]
        self.reserveDate = datetime.strptime(
            config["reserveDate"], "%Y-%m-%d"
        ).strftime("%Y-%m-%d")
        self.reservePlace = config["reservePlace"]
        self.reserveList = config["reserveList"]
        self.apiUrls = config["apiUrls"]

    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(requests.RequestException),
    )
    def _get_field_id(headers, proxies, url):
        place_url = url
        response = requests.get(url=place_url, headers=headers, proxies=proxies)
        return {
            "九里": response.json()["fieldList"][0]["id"],
            "犀浦": response.json()["fieldList"][1]["id"],
        }

    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(0.2),
        retry=retry_if_exception_type(requests.RequestException),
    )
    def getLibraryInfo(headers, proxies, reserveDate, reservePlace, apiUrls) -> Result:
        if reservePlace in SportsFacilityReservation.session_cache:
            logging.info(f"使用缓存的场地信息: {reservePlace}")
            return Result.success(SportsFacilityReservation.session_cache[reservePlace])

        try:
            if reservePlace not in SportsFacilityReservation.field_cache:
                fieldId = SportsFacilityReservation._get_field_id(
                    headers, proxies, apiUrls["place_url"]
                )
                SportsFacilityReservation.field_cache = fieldId
                logging.info(f"场地缓存已更新: {fieldId}")
            weChatSessionsListUrl = apiUrls["session_list_url"]
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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(0.02),
        retry=retry_if_exception_type(requests.RequestException),
    )
    def reserveField(self) -> List[Result]:
        fieldResult = self.getLibraryInfo(
            self.headers,
            self.proxies,
            self.reserveDate,
            self.reservePlace,
            self.apiUrls,
        )

        if fieldResult["code"] != 0:
            logging.error(f"获取场地信息失败: {fieldResult['message']}")
            return [Result.error(fieldResult["message"])]

        sessionList = fieldResult["data"][self.reservePlace]
        requestsLists = [
            {"sessionsId": sessionList[col][row]["id"]} for row, col in self.reserveList
        ]
        reserveUrl = self.apiUrls["reserve_url"]
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


def process_user(user, apiUrls):
    user["reserveDate"] = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    logging.info(
        f"当前用户：{user['headers']['X-UserToken']}，预约日期：{user['reserveDate']}"
    )
    user["apiUrls"] = apiUrls
    reservation = SportsFacilityReservation(user)
    reserveResults = reservation.reserveField()
    for reserveResult in reserveResults:
        message = reserveResult["message"]
        logging.info(f"预约结果: {message}")


def main():
    config = load_config()
    apiUrls = config["apiUrls"]
    users = config["users"]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_user, user, apiUrls) for user in users]
        for future in concurrent.futures.as_completed(futures):
            future.result()


if __name__ == "__main__":
    main()
