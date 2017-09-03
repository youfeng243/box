# -*- coding: utf-8 -*-

from datetime import datetime

from flask import Blueprint, request, g, redirect

from box.account.model import User
from box.collecation.model import Collecation, Mode, gen_item_id
from box.const import HTTP_BAD_REQUEST
from box.ext import db
from box.order.model import Order
from box.payment.model import Payment
from box.pocket.model import Pocket
from box.utils.api import success, fail
from box.wechat.auth import wechat_login
from box.wechat.event import handle_events
from box.wechat.order import XMLData, query_order_from_wechat
from box.wechat.signature import check_signature

bp = Blueprint('wechat', __name__)
bp.before_request(wechat_login)


@bp.route('/', methods=['GET', 'POST'])
@check_signature
def index():
    if request.method == 'GET':
        return request.args.get('echostr')
    elif request.method == 'POST':
        return handle_events(request.data)


@bp.route('/wechat/entry/<name>', methods=['GET'])
def entry(name):
    if g.wechat_openid is None:
        return "Login Failed"

    user = User.get_by_openid(g.wechat_openid)
    if user is None:
        return redirect('/bind')

    if name == 'product':
        return redirect('/buy')

    if name == 'collecation':
        return redirect('/order')

    if name == 'help':
        return 'help: ' + g.wechat_openid

    if name == 'mine':
        return redirect('/account/box')


@bp.route('/wechat/payment/callback', methods=['POST'])
def callback():
    data = XMLData.parse(request.data)

    if data.return_code == 'SUCCESS' and data.result_code == 'SUCCESS':
        payment_no = data.out_trade_no
        transaction_id = data.transaction_id
        paid_at = datetime.strptime(data.time_end, '%Y%m%d%H%M%S')

        payment = Payment.get_by_payment_no(payment_no)
        if payment is not None and payment.status != Payment.STATUS_PAID:
            wechat_transaction = query_order_from_wechat(transaction_id)
            if wechat_transaction is None:
                return fail(HTTP_BAD_REQUEST)

            if (wechat_transaction.return_code == 'SUCCESS' and
                        wechat_transaction.result_code == 'SUCCESS'):

                remark = payment.remark
                remark['wechat_transaction_id'] = transaction_id
                payment.remark = remark

                payment.paid_at = paid_at
                payment.status = Payment.STATUS_PAID
                db.session.add(payment)

                if payment.payment_type == Payment.TYPE_RECHARGE:
                    pocket = Pocket.get_or_create_by_user_id(payment.user_id)
                    pocket.add(payment.amount)

                elif payment.payment_type == Payment.TYPE_BUY:
                    order = Order.get_by_payment_id(payment.id)
                    if order is None:
                        return fail(HTTP_BAD_REQUEST)

                    items = order.get_items()
                    for each in items:
                        if each.item_id is None:
                            item_id = gen_item_id(payment.user_id)
                            Collecation.create(
                                user_id=payment.user_id,
                                mode_id=Mode.get_default_id(),
                                item_id=item_id)
                            each.item_id = item_id
                            db.session.add(each)
                    order.status = Order.STATUS_PAYED
                    order.payment_method = Order.PAYED_WECHAT
                    db.session.add(order)

                db.session.commit()
                return success()

    return fail(HTTP_BAD_REQUEST)
