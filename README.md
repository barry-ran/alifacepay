# alifacepay
支付宝当面付sdk封装

[支付宝当面付](https://blog.csdn.net/rankun1/article/details/92401295)支持个人申请，无需企业认证

# 描述
基于[蚂蚁金服开放平台 Python SDK](https://github.com/alipay/alipay-sdk-python-all)封装了当面付（扫码支付）常用操作，使用非常简单，在支付宝开发平台配置好应用的公钥后（[配置流程](https://blog.csdn.net/rankun1/article/details/92401295)），配置三个参数即可体验支付流程。当然，别忘了安装requirements.txt里的依赖包。

# 代码示例
```
    # 基础信息配置
    # 只需要三个关键信息 app_id，alipay_public_key，app_private_key
    sandbox = True
    if sandbox:
        app_id = '2016092900626816'
        alipay_public_key_string = open("../alipay_public_key_sandbox.txt").read()
    else:
        app_id = '2019061665605123'
        alipay_public_key_string = open("../alipay_public_key.txt").read()

    app_private_key_string = open("../app_private_key.pem").read()

    pay = AliFacePay(app_id, app_private_key_string, alipay_public_key_string, sandbox)

    out_trade_no = 'out_trade_no20190616_13'
    #out_trade_no = AliFacePay.gen_trade_no('yqhs')

    # print(pay.cancel(out_trade_no))
    # print(pay.close(out_trade_no))
    # print(pay.refund(out_trade_no, 1))
    # print(pay.query(out_trade_no))
    # exit()

    start = time.time()

    # 生成付款二维码，可以去这里生成qr_code的二维码图片 http://www.liantu.com/
    qr_code = pay.precreate(out_trade_no, 1, "测试")

    end = time.time()
    print(end - start)

    if qr_code:
        print(qr_code)
        # 查询订单状态
        paid = False
        for i in range(20):
            # 最佳实践：每隔3s轮询，总轮询60s，未付款则取消订单
            time.sleep(3)
            query_result = pay.query(out_trade_no)
            print(query_result.get("trade_status", ""))
            if query_result.get("trade_status", "") == "TRADE_SUCCESS":
                paid = True
                print("支付成功")
                break
            elif query_result.get("trade_status", "") == "WAIT_BUYER_PAY":
                print("等待用户支付")
            else:
                print("等待用户扫描付款二维码")

        if paid:
            print("退款")
            print(pay.refund(out_trade_no, 1))
        else:
            print("取消订单")
            pay.cancel(out_trade_no)

    else:
        print('付款二维码生成失败')
```
