#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import traceback
from random import randint
import time

# api文档 https://docs.open.alipay.com/194/105203
from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient

# alipay.trade.precreate
from alipay.aop.api.domain.AlipayTradePrecreateModel import AlipayTradePrecreateModel
from alipay.aop.api.request.AlipayTradePrecreateRequest import AlipayTradePrecreateRequest
from alipay.aop.api.response.AlipayTradePrecreateResponse import AlipayTradePrecreateResponse

# alipay.trade.query
from alipay.aop.api.domain.AlipayTradeQueryModel import AlipayTradeQueryModel
from alipay.aop.api.request.AlipayTradeQueryRequest import AlipayTradeQueryRequest
from alipay.aop.api.response.AlipayTradeQueryResponse import AlipayTradeQueryResponse

# alipay.trade.cancel
from alipay.aop.api.domain.AlipayTradeCancelModel import AlipayTradeCancelModel
from alipay.aop.api.request.AlipayTradeCancelRequest import AlipayTradeCancelRequest
from alipay.aop.api.response.AlipayTradeCancelResponse import AlipayTradeCancelResponse

# alipay.trade.close
from alipay.aop.api.domain.AlipayTradeCloseModel import AlipayTradeCloseModel
from alipay.aop.api.request.AlipayTradeCloseRequest import AlipayTradeCloseRequest
from alipay.aop.api.response.AlipayTradeCloseResponse import AlipayTradeCloseResponse

# alipay.trade.refund
from alipay.aop.api.domain.AlipayTradeRefundModel import AlipayTradeRefundModel
from alipay.aop.api.request.AlipayTradeRefundRequest import AlipayTradeRefundRequest
from alipay.aop.api.response.AlipayTradeRefundResponse import AlipayTradeRefundResponse

logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        filemode='a', )

'''
1. 通过预下单接口生成的二维码有效时间为2小时
2. 可退款期限根据签约协议确定，一般为三个月或十二个月
3. 对于未支付的订单，请及时通过调用撤销接口关闭订单（注意：超过24小时的订单无法撤销）；
另外一种方法是为每笔订单设置超时时间，超过时间未支付的订单会自动关闭。
'''
class AliFacePay:
    logger = logging.getLogger('')

    def __init__(self, app_id, app_private_key, alipay_public_key, sandbox_debug=False):
        '''
        设置配置，包括支付宝网关地址、app_id、应用私钥、支付宝公钥等，其他配置值可以查看AlipayClientConfig的定义。
        '''
        alipay_client_config = AlipayClientConfig(sandbox_debug=sandbox_debug)
        alipay_client_config.app_id = app_id
        alipay_client_config.app_private_key = app_private_key
        alipay_client_config.alipay_public_key = alipay_public_key

        '''
        得到客户端对象。
        注意，一个alipay_client_config对象对应一个DefaultAlipayClient，定义DefaultAlipayClient对象后，alipay_client_config不得修改，如果想使用不同的配置，请定义不同的DefaultAlipayClient。
        logger参数用于打印日志，不传则不打印，建议传递。
        '''
        self.client = DefaultAlipayClient(alipay_client_config=alipay_client_config, logger=AliFacePay.logger)

    '''
    功能：生成支付二维码，生成二维码后，展示给用户，由用户扫描二维码创建支付订单
    
    参数：
    out_trade_no：订单号，不可重复，用来区分每一笔订单
    total_amount：订单金额，单位元，精确到小数点后2位
    subject：订单标题
    body：订单详细描述
    
    返回值：string 付款二维码链接，使用二维码生成工具生成二维码提供给用户付款
    '''
    def precreate(self, out_trade_no, total_amount, subject, body=None):
        '''
        系统接口示例：alipay.trade.precreate
        '''
        # 对照接口文档，构造请求对象
        precreate_model = AlipayTradePrecreateModel()
        precreate_model.out_trade_no = out_trade_no
        precreate_model.total_amount = total_amount
        precreate_model.subject = subject
        # 该笔订单允许的最晚付款时间，逾期将自动关闭交易(TRADE_CLOSED),时间从用户扫描付款二维码以后开始计算
        precreate_model.timeout_express = '2m'

        # 花呗，默认支持吗？
        #precreate_model.enable_pay_channels = 'pcredit'
        # 花呗分期
        #precreate_model.enable_pay_channels = 'pcreditpayInstallment'

        if body:
            precreate_model.body = body

        precreate_request = AlipayTradePrecreateRequest(biz_model=precreate_model)
        precreate_response_content = None
        qr_code = None
        try:
            precreate_response_content = self.client.execute(precreate_request)
        except Exception as e:
            print(traceback.format_exc())

        if not precreate_response_content:
            print("failed execute precreate")
        else:
            precreate_response = AlipayTradePrecreateResponse()
            # 解析响应结果
            precreate_response.parse_response_content(precreate_response_content)
            if precreate_response.is_success():
                # 如果业务成功，则通过respnse属性获取需要的值
                qr_code = precreate_response.qr_code
                # print("get response out_trade_no:" + precreate_response.out_trade_no)
                # print("get response qr_code:" + precreate_response.qr_code)
            else:
                # 如果业务失败，则从错误码中可以得知错误情况，具体错误码信息可以查看接口文档
                print(precreate_response.code + "," + precreate_response.msg + "," + precreate_response.sub_code + ","
                      + precreate_response.sub_msg)
        return qr_code

    '''
    功能：主动查询订单状态(只有用户扫描了二维码以后才会创建订单，用户扫描之前得到的结果会是 40004 交易不存在)

    参数：
    out_trade_no：订单号，不可重复，用来区分每一笔订单        

    返回值：dict
    out_trade_no：订单号
    buyer_logon_id：买家支付宝账号
    trade_status：交易状态：WAIT_BUYER_PAY（交易创建，等待买家付款）、TRADE_CLOSED（未付款交易超时关闭，或支付完成后全额退款）、TRADE_SUCCESS（交易支付成功）、TRADE_FINISHED（交易结束，不可退款）
    total_amount：交易金额
    '''
    def query(self, out_trade_no):
        '''
        系统接口示例：alipay.trade.query
        '''
        # 对照接口文档，构造请求对象
        query_model = AlipayTradeQueryModel()
        query_model.out_trade_no = out_trade_no

        query_request = AlipayTradeQueryRequest(biz_model=query_model)
        query_response_content = None
        ret_dict = {}
        try:
            query_response_content = self.client.execute(query_request)
        except Exception as e:
            print(traceback.format_exc())

        if not query_response_content:
            print("failed execute query")
        else:
            query_response = AlipayTradeQueryResponse()
            # 解析响应结果
            query_response.parse_response_content(query_response_content)
            if query_response.is_success():
                # 如果业务成功，则通过respnse属性获取需要的值
                ret_dict['out_trade_no'] = query_response.out_trade_no
                ret_dict['buyer_logon_id'] = query_response.buyer_logon_id
                ret_dict['trade_status'] = query_response.trade_status
                ret_dict['total_amount'] = query_response.total_amount
            else:
                # 如果业务失败，则从错误码中可以得知错误情况，具体错误码信息可以查看接口文档
                print(query_response.code + "," + query_response.msg + "," + query_response.sub_code + ","
                      + query_response.sub_msg)
        return ret_dict

    '''
    功能：支付交易返回失败或支付系统超时，调用该接口撤销交易。
    cancel和close的区别是，交易完成后不可以close，但是可以cancel，cancel会退款给用户
    生成二维码之后，扫描之前也可以cancel，但是不可以close

    参数：
    out_trade_no：订单号，不可重复，用来区分每一笔订单
        
    返回值：bool 是否执行成功
    '''
    def cancel(self, out_trade_no):
        '''
        系统接口示例：alipay.trade.cancel
        '''
        # 对照接口文档，构造请求对象
        cancel_model = AlipayTradeCancelModel()
        cancel_model.out_trade_no = out_trade_no

        cancel_request = AlipayTradeCancelRequest(biz_model=cancel_model)
        cancel_response_content = None
        ret = False
        try:
            cancel_response_content = self.client.execute(cancel_request)
        except Exception as e:
            print(traceback.format_exc())

        if not cancel_response_content:
            print("failed execute cancel")
        else:
            cancel_response = AlipayTradeCancelResponse()
            # 解析响应结果
            cancel_response.parse_response_content(cancel_response_content)
            if cancel_response.is_success():
                # 如果业务成功，则通过respnse属性获取需要的值
                ret = True
            else:
                # 如果业务失败，则从错误码中可以得知错误情况，具体错误码信息可以查看接口文档
                print(cancel_response.code + "," + cancel_response.msg + "," + cancel_response.sub_code + ","
                      + cancel_response.sub_msg)
        return ret

    '''
    功能：用于交易创建后，用户在一定时间内未进行支付，可调用该接口直接将未付款的交易进行关闭。
    也就是用户扫码创建了订单，用户支付之前我们可以close订单
    也就是说当且仅当订单状态为WAIT_BUYER_PAY时可以close

    参数：
    out_trade_no：订单号，不可重复，用来区分每一笔订单

    返回值：bool 是否执行成功
    '''
    def close(self, out_trade_no):
        '''
        系统接口示例：alipay.trade.cancel
        '''
        # 对照接口文档，构造请求对象
        close_model = AlipayTradeCloseModel()
        close_model.out_trade_no = out_trade_no

        close_request = AlipayTradeCloseRequest(biz_model=close_model)
        close_response_content = None
        ret = False
        try:
            close_response_content = self.client.execute(close_request)
        except Exception as e:
            print(traceback.format_exc())

        if not close_response_content:
            print("failed execute close")
        else:
            close_response = AlipayTradeCloseResponse()
            # 解析响应结果
            close_response.parse_response_content(close_response_content)
            if close_response.is_success():
                # 如果业务成功，则通过respnse属性获取需要的值
                ret = True
            else:
                # 如果业务失败，则从错误码中可以得知错误情况，具体错误码信息可以查看接口文档
                print(close_response.code + "," + close_response.msg + "," + close_response.sub_code + ","
                      + close_response.sub_msg)
        return ret

    '''
    功能：退款

    参数：
    out_trade_no：订单号，不可重复，用来区分每一笔订单

    返回值：bool 是否执行成功
    '''
    def refund(self, out_trade_no, refund_amount):
        '''
        系统接口示例：alipay.trade.refund
        '''
        # 对照接口文档，构造请求对象
        refund_model = AlipayTradeRefundModel()
        refund_model.out_trade_no = out_trade_no
        refund_model.refund_amount = refund_amount

        refund_request = AlipayTradeRefundRequest(biz_model=refund_model)
        refund_response_content = None
        ret = False
        try:
            refund_response_content = self.client.execute(refund_request)
        except Exception as e:
            print(traceback.format_exc())

        if not refund_response_content:
            print("failed execute refund")
        else:
            refund_response = AlipayTradeRefundResponse()
            # 解析响应结果
            refund_response.parse_response_content(refund_response_content)
            if refund_response.is_success():
                # 如果业务成功，则通过respnse属性获取需要的值
                ret = True
                # print("get response out_trade_no:" + refund_response.out_trade_no)
                # print("get response refund_fee:" + refund_response.refund_fee)
            else:
                # 如果业务失败，则从错误码中可以得知错误情况，具体错误码信息可以查看接口文档
                print(refund_response.code + "," + refund_response.msg + "," + refund_response.sub_code + ","
                      + refund_response.sub_msg)
        return ret

    @classmethod
    def get_rand_string(cls, length=10):
        # 生成len长度的随机字符串
        s = ""
        for _ in range(length):
            s = s + str(randint(0, 9))
        return s

    @classmethod
    def gen_trade_no(cls, pre_string=None):
        timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))
        trade_no = timestamp + cls.get_rand_string()
        if pre_string:
            trade_no = pre_string + '_' + trade_no
        return trade_no


if __name__ == "__main__":
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
