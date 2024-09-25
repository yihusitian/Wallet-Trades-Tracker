from dotenv import load_dotenv
import os

import requests

load_dotenv(os.path.join(os.getcwd(), '.env\.env'))
company_wechat_webhook_id = os.getenv("company_wechat_webhook_id")

async def send_company_wechat_message(swap_infos: dict):
    if company_wechat_webhook_id is None:
        print("未配置company_wechat_webhook_id")
        return
    webhook_url = f"'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={company_wechat_webhook_id}"

    message = (
        f"✨ <a href='{swap_infos['LINKS']['SCAN']['TRANSACTION']}'>{swap_infos['CHAIN']} - {swap_infos['MAKER_INFOS']['SHORT_ADDRESS']}</a>\n" +
        f"👤 <a href='{swap_infos['LINKS']['SCAN']['MAKER']}'>{swap_infos['MAKER_INFOS']['SHORT_ADDRESS']}</a>\n" +
        f"📜 <a href='{swap_infos['LINKS']['SCAN']['TRANSACTION']}'>TX</a>\n\n"
    )
    for swap_id, swap_infos in swap_infos['SWAPS'].items():
        emoji_swap_id = await get_emoji_swap_id(swap_id=swap_id)
        message += (
            f"{emoji_swap_id} SWAP {swap_infos['SYMBOLS']['TOKEN0']} » {swap_infos['SYMBOLS']['TOKEN1']}\n" +
            f"• 💵 {swap_infos['AMOUNTS']['TOKEN0']} ${swap_infos['SYMBOLS']['TOKEN0']} » {swap_infos['AMOUNTS']['TOKEN1']} ${swap_infos['SYMBOLS']['TOKEN1']}\n" +
            f"• 📊 <a href='{swap_infos['LINKS']['CHART']}'>CHART/TRADING</a>\n"
        )
    payload = {
        "msgtype": 'markdown',
        "markdown": {
            "content": message
        }
    }

    try:
        requests.post(url=webhook_url, data=payload)
    except:
        print("[!] Couldn't send CompanyWechat message.")

async def get_emoji_swap_id(swap_id: int) -> str:
    """
    Returns an emoji for the swap ID.

    Parameters:
        ``swap_id (int)``: id of the swap
    """

    swap_id_emoji = (
        "1️⃣" if swap_id == 1 else
        "2️⃣" if swap_id == 2 else
        "3️⃣" if swap_id == 3 else
        "4️⃣" if swap_id == 4 else
        "5️⃣" if swap_id == 5 else
        "6️⃣" if swap_id == 6 else
        "7️⃣" if swap_id == 7 else
        "8️⃣" if swap_id == 8 else
        "9️⃣" if swap_id == 9 else
        "1️⃣0️⃣" if swap_id == 10 else
        "1️⃣1️⃣" if swap_id == 11 else
        "1️⃣2️⃣" if swap_id == 12 else
        "1️⃣3️⃣" if swap_id == 13 else
        "1️⃣4️⃣" if swap_id == 14 else
        "1️⃣5️⃣" if swap_id == 15 else
        "1️⃣6️⃣" if swap_id == 16 else
        "1️⃣7️⃣" if swap_id == 17 else
        "1️⃣8️⃣" if swap_id == 18 else
        "1️⃣9️⃣" if swap_id == 19 else
        "2️⃣0️⃣" if swap_id == 20 else
        "🔢"
    )
    return swap_id_emoji

    # try:
    #     data = {
    #         "msgtype": "text",
    #         "text": {
    #             "content": content + '\n' + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #         }
    #     }
    #     r = requests.post(url, data=json.dumps(data), timeout=10)
    #     print(f'调用企业微信接口返回： {r.text}')
    #     print('成功发送企业微信')
    # except Exception as e:
    #     print(f"发送企业微信失败:{e}")
    #     print(traceback.format_exc())
