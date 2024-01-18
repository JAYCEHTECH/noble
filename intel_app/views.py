import hashlib
import hmac
import json
from datetime import datetime

from decouple import config
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
import requests
from django.views.decorators.csrf import csrf_exempt

from . import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from . import helper, models


# Create your views here.
def home(request):
    return render(request, "layouts/index.html")


def services(request):
    return render(request, "layouts/services.html")


def pay_with_wallet(request):
    if request.method == "POST":
        admin = models.AdminInfo.objects.filter().first().phone_number
        user = models.CustomUser.objects.get(id=request.user.id)
        phone_number = request.POST.get("phone")
        amount = request.POST.get("amount")
        reference = request.POST.get("reference")
        if user.wallet is None:
            return JsonResponse({'status': f'Your wallet balance is low. Contact the admin to recharge. Admin Contact Info: 0{admin}'})
        elif user.wallet <= 0 or user.wallet < float(amount):
            return JsonResponse({'status': f'Your wallet balance is low. Contact the admin to recharge. Admin Contact Info: 0{admin}'})
        print(phone_number)
        print(amount)
        print(reference)
        bundle = models.IshareBundlePrice.objects.get(price=float(amount)).bundle_volume if user.status == "User" else models.AgentIshareBundlePrice.objects.get(price=float(amount)).bundle_volume
        print(bundle)
        send_bundle_response = helper.send_bundle(request.user, phone_number, bundle, reference)
        data = send_bundle_response.json()
        print(data)

        sms_headers = {
            'Authorization': 'Bearer 1050|VDqcCUHwCBEbjcMk32cbdOhCFlavpDhy6vfgM4jU',
            'Content-Type': 'application/json'
        }

        sms_url = 'https://webapp.usmsgh.com/api/sms/send'
        if send_bundle_response.status_code == 200:
            if data["code"] == "0000":
                new_transaction = models.IShareBundleTransaction.objects.create(
                    user=request.user,
                    bundle_number=phone_number,
                    offer=f"{bundle}MB",
                    reference=reference,
                    transaction_status="Completed"
                )
                new_transaction.save()
                user.wallet -= float(amount)
                user.save()
                receiver_message = f"Your bundle purchase has been completed successfully. {bundle}MB has been credited to you by {request.user.phone}.\nReference: {reference}\n"
                sms_message = f"Hello @{request.user.username}. Your bundle purchase has been completed successfully. {bundle}MB has been credited to {phone_number}.\nReference: {reference}\nCurrent Wallet Balance: {user.wallet}\nThank you for using Noble Data GH.\n\nThe Noble Data GH"

                num_without_0 = phone_number[1:]
                print(num_without_0)
                receiver_body = {
                    'recipient': f"233{num_without_0}",
                    'sender_id': 'Noble Data',
                    'message': receiver_message
                }

                response = requests.request('POST', url=sms_url, params=receiver_body, headers=sms_headers)
                print(response.text)

                sms_body = {
                    'recipient': f"233{request.user.phone}",
                    'sender_id': 'Noble Data',
                    'message': sms_message
                }

                response = requests.request('POST', url=sms_url, params=sms_body, headers=sms_headers)

                print(response.text)

                return JsonResponse({'status': 'Transaction Completed Successfully', 'icon': 'success'})
            else:
                new_transaction = models.IShareBundleTransaction.objects.create(
                    user=request.user,
                    bundle_number=phone_number,
                    offer=f"{bundle}MB",
                    reference=reference,
                    transaction_status="Failed"
                )
                new_transaction.save()
                return JsonResponse({'status': 'Something went wrong'})
    return redirect('airtel-tigo')


@login_required(login_url='login')
def airtel_tigo(request):
    user = models.CustomUser.objects.get(id=request.user.id)
    db_user_id = request.user.id
    status = user.status
    form = forms.IShareBundleForm(status)
    reference = helper.ref_generator()
    user_email = request.user.email
    if request.method == "POST":
        form = forms.IShareBundleForm(data=request.POST, status=status)
        payment_reference = request.POST.get("reference")
        amount_paid = request.POST.get("amount")
        new_payment = models.Payment.objects.create(
            user=request.user,
            reference=payment_reference,
            amount=amount_paid,
            transaction_date=datetime.now(),
            transaction_status="Completed"
        )
        new_payment.save()
        print("payment saved")
        print("form valid")
        phone_number = request.POST.get("phone")
        offer = request.POST.get("amount")
        print(offer)
        bundle = models.IshareBundlePrice.objects.get(price=float(offer)).bundle_volume if user.status == "User" else models.AgentIshareBundlePrice.objects.get(price=float(offer)).bundle_volume
        new_transaction = models.IShareBundleTransaction.objects.create(
            user=request.user,
            bundle_number=phone_number,
            offer=f"{bundle}MB",
            reference=payment_reference,
            transaction_status="Pending"
        )
        print("created")
        new_transaction.save()

        print("===========================")
        print(phone_number)
        print(bundle)
        send_bundle_response = helper.send_bundle(request.user, phone_number, bundle, payment_reference)
        data = send_bundle_response.json()

        print(data)

        sms_headers = {
            'Authorization': 'Bearer 1050|VDqcCUHwCBEbjcMk32cbdOhCFlavpDhy6vfgM4jU',
            'Content-Type': 'application/json'
        }

        sms_url = 'https://webapp.usmsgh.com/api/sms/send'

        if send_bundle_response.status_code == 200:
            if data["code"] == "0000":
                transaction_to_be_updated = models.IShareBundleTransaction.objects.get(reference=payment_reference)
                print("got here")
                print(transaction_to_be_updated.transaction_status)
                transaction_to_be_updated.transaction_status = "Completed"
                transaction_to_be_updated.save()
                print(request.user.phone)
                print("***********")
                receiver_message = f"Your bundle purchase has been completed successfully. {bundle}MB has been credited to you by {request.user.phone}.\nReference: {payment_reference}\n"
                sms_message = f"Hello @{request.user.username}. Your bundle purchase has been completed successfully. {bundle}MB has been credited to {phone_number}.\nReference: {payment_reference}\nThank you for using Noble Data GH.\n\nThe Noble Data GH"

                num_without_0 = phone_number[1:]
                print(num_without_0)
                receiver_body = {
                    'recipient': f"233{num_without_0}",
                    'sender_id': 'Noble Data',
                    'message': receiver_message
                }

                response = requests.request('POST', url=sms_url, params=receiver_body, headers=sms_headers)
                print(response.text)

                sms_body = {
                    'recipient': f"233{request.user.phone}",
                    'sender_id': 'Noble Data',
                    'message': sms_message
                }

                response = requests.request('POST', url=sms_url, params=sms_body, headers=sms_headers)

                print(response.text)

                return JsonResponse({'status': 'Transaction Completed Successfully', 'icon': 'success'})
            else:
                transaction_to_be_updated = models.IShareBundleTransaction.objects.get(reference=payment_reference)
                transaction_to_be_updated.transaction_status = "Failed"
                new_transaction.save()
                sms_message = f"Hello @{request.user.username}. Something went wrong with your transaction. Contact us for enquiries.\nBundle: {bundle}MB\nPhone Number: {phone_number}.\nReference: {payment_reference}\nThank you for using Noble Data GH.\n\nThe Noble Data GH"

                sms_body = {
                    'recipient': f"233{request.user.phone}",
                    'sender_id': 'Noble Data',
                    'message': sms_message
                }
                response = requests.request('POST', url=sms_url, params=sms_body, headers=sms_headers)
                print(response.text)
                # r_sms_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key=UmpEc1JzeFV4cERKTWxUWktqZEs&to={phone_number}&from=Noble Data GH&sms={receiver_message}"
                # response = requests.request("GET", url=r_sms_url)
                # print(response.text)
                return JsonResponse({'status': 'Something went wrong', 'icon': 'error'})
        else:
            transaction_to_be_updated = models.IShareBundleTransaction.objects.get(reference=payment_reference)
            transaction_to_be_updated.transaction_status = "Failed"
            new_transaction.save()
            sms_message = f"Hello @{request.user.username}. Something went wrong with your transaction. Contact us for enquiries.\nBundle: {bundle}MB\nPhone Number: {phone_number}.\nReference: {payment_reference}\nThank you for using Noble Data GH.\n\nThe Noble Data GH"

            sms_body = {
                'recipient': f'233{request.user.phone}',
                'sender_id': 'Noble Data',
                'message': sms_message
            }

            response = requests.request('POST', url=sms_url, params=sms_body, headers=sms_headers)

            print(response.text)
            return JsonResponse({'status': 'Something went wrong', 'icon': 'error'})
    user = models.CustomUser.objects.get(id=request.user.id)
    context = {"form": form, 'id': db_user_id, "ref": reference, "email": user_email, "wallet": 0 if user.wallet is None else user.wallet }
    return render(request, "layouts/services/at.html", context=context)


def mtn_pay_with_wallet(request):
    if request.method == "POST":
        user = models.CustomUser.objects.get(id=request.user.id)
        phone = user.phone
        phone_number = request.POST.get("phone")
        amount = request.POST.get("amount")
        reference = request.POST.get("reference")
        print(phone_number)
        print(amount)
        auth = config("AT")
        user_id = config("USER_ID")
        print(reference)
        sms_headers = {
            'Authorization': 'Bearer 1050|VDqcCUHwCBEbjcMk32cbdOhCFlavpDhy6vfgM4jU',
            'Content-Type': 'application/json'
        }

        sms_url = 'https://webapp.usmsgh.com/api/sms/send'
        admin = models.AdminInfo.objects.filter().first().phone_number

        if user.wallet is None:
            return JsonResponse({'status': f'Your wallet balance is low. Contact the admin to recharge. Admin Contact Info: 0{admin}'})
        elif user.wallet <= 0 or user.wallet < float(amount):
            return JsonResponse({'status': f'Your wallet balance is low. Contact the admin to recharge. Admin Contact Info: 0{admin}'})
        bundle = models.MTNBundlePrice.objects.get(price=float(amount)).bundle_volume if user.status == "User" else models.AgentMTNBundlePrice.objects.get(price=float(amount)).bundle_volume

        url = "https://posapi.bestpaygh.com/api/v1/initiate_mtn_transaction"

        payload = json.dumps({
            "user_id": user_id,
            "receiver": phone_number,
            "data_volume": bundle,
            "reference": reference,
            "amount": amount,
            "channel": phone
        })
        print(auth)
        headers = {
            'Authorization': auth,
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        print(response.text)
        print(bundle)
        sms_message = f"An order has been placed. {bundle}MB for {phone_number}"
        new_mtn_transaction = models.MTNTransaction.objects.create(
            user=request.user,
            bundle_number=phone_number,
            offer=f"{bundle}MB",
            reference=reference,
        )
        new_mtn_transaction.save()
        user.wallet -= float(amount)
        user.save()
        return JsonResponse({'status': "Your transaction will be completed shortly", 'icon': 'success'})
    return redirect('mtn')


@login_required(login_url='login')
def mtn(request):
    user = models.CustomUser.objects.get(id=request.user.id)
    db_user_id = request.user.id
    phone = user.phone
    status = user.status
    form = forms.MTNForm(status=status)
    reference = helper.ref_generator()
    user_email = request.user.email
    auth = config("AT")
    user_id = config("USER_ID")
    if request.method == "POST":
        payment_reference = request.POST.get("reference")
        amount_paid = request.POST.get("amount")
        new_payment = models.Payment.objects.create(
            user=request.user,
            reference=payment_reference,
            amount=amount_paid,
            transaction_date=datetime.now(),
            transaction_status="Completed"
        )
        new_payment.save()
        phone_number = request.POST.get("phone")
        offer = request.POST.get("amount")

        bundle = models.MTNBundlePrice.objects.get(price=float(offer)).bundle_volume if user.status == "User" else models.AgentMTNBundlePrice.objects.get(price=float(offer)).bundle_volume
        url = "https://posapi.bestpaygh.com/api/v1/initiate_mtn_transaction"

        payload = json.dumps({
            "user_id": user_id,
            "receiver": phone_number,
            "data_volume": bundle,
            "reference": reference,
            "amount": offer,
            "channel": phone
        })
        headers = {
            'Authorization': auth,
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        print(response.text)
        print(phone_number)
        new_mtn_transaction = models.MTNTransaction.objects.create(
            user=request.user,
            bundle_number=phone_number,
            offer=f"{bundle}MB",
            reference=payment_reference,
        )
        new_mtn_transaction.save()
        # sms_headers = {
        #     'Authorization': 'Bearer 1050|VDqcCUHwCBEbjcMk32cbdOhCFlavpDhy6vfgM4jU',
        #     'Content-Type': 'application/json'
        # }
        #
        # sms_url = 'https://webapp.usmsgh.com/api/sms/send'
        # sms_message = f"An order has been placed. {bundle}MB for {phone_number}"
        # admin = models.AdminInfo.objects.filter().first().phone_number
        # sms_body = {
        #     'recipient': f"233{admin}",
        #     'sender_id': 'Noble Data',
        #     'message': sms_message
        # }
        # response = requests.request('POST', url=sms_url, params=sms_body, headers=sms_headers)
        # print(response.text)
        return JsonResponse({'status': "Your transaction will be completed shortly", 'icon': 'success'})
    user = models.CustomUser.objects.get(id=request.user.id)
    phone_num = user.phone
    mtn_dict = {}

    if user.status == "Agent":
        mtn_offer = models.AgentMTNBundlePrice.objects.all()
    else:
        mtn_offer = models.MTNBundlePrice.objects.all()
    for offer in mtn_offer:
        mtn_dict[str(offer)] = offer.bundle_volume
    context = {'form': form, 'phone_num': phone_num, 'id': db_user_id, 'auth': auth, 'user_id': user_id, 'mtn_dict': json.dumps(mtn_dict), "ref": reference, "email": user_email, "wallet": 0 if user.wallet is None else user.wallet}
    return render(request, "layouts/services/mtn.html", context=context)


@csrf_exempt
def paystack_webhook(request):
    if request.method == "POST":
        paystack_secret_key = config("PAYSTACK_SECRET_KEY")
        # print(paystack_secret_key)
        payload = json.loads(request.body)

        paystack_signature = request.headers.get("X-Paystack-Signature")

        if not paystack_secret_key or not paystack_signature:
            return HttpResponse(status=400)

        computed_signature = hmac.new(
            paystack_secret_key.encode('utf-8'),
            request.body,
            hashlib.sha512
        ).hexdigest()

        if computed_signature == paystack_signature:
            print("yes")
            print(payload.get('data'))
            r_data = payload.get('data')
            print(r_data.get('metadata'))
            print(payload.get('event'))
            if payload.get('event') == 'charge.success':
                metadata = r_data.get('metadata')
                receiver = metadata.get('receiver')
                db_id = metadata.get('db_id')
                print(db_id)
                offer = metadata.get('offer')
                user = models.CustomUser.objects.get(id=int(db_id))
                print(user)
                channel = metadata.get('channel')
                real_amount = metadata.get('real_amount')
                print(real_amount)
                paid_amount = r_data.get('amount')
                reference = r_data.get('reference')

                if channel == "ishare":
                    bundle = models.IshareBundlePrice.objects.get(price=float(
                        real_amount)).bundle_volume if user.status == "User" else models.AgentIshareBundlePrice.objects.get(
                        price=float(real_amount)).bundle_volume
                    if models.IShareBundleTransaction.objects.filter(reference=reference, offer=f"{bundle}MB", transaction_status="Completed").exists():
                        return HttpResponse(status=200)
                    new_transaction = models.IShareBundleTransaction.objects.create(
                        user=user,
                        bundle_number=receiver,
                        offer=f"{bundle}MB",
                        reference=reference,
                        transaction_status="Pending"
                    )
                    new_transaction.save()
                    send_bundle_response = helper.send_bundle(user, receiver, bundle, reference)
                    data = send_bundle_response.json()

                    print(data)

                    sms_headers = {
                        'Authorization': 'Bearer 1050|VDqcCUHwCBEbjcMk32cbdOhCFlavpDhy6vfgM4jU',
                        'Content-Type': 'application/json'
                    }

                    sms_url = 'https://webapp.usmsgh.com/api/sms/send'

                    if send_bundle_response.status_code == 200:
                        if data["code"] == "0000":
                            transaction_to_be_updated = models.IShareBundleTransaction.objects.get(
                                reference=reference)
                            print("got here")
                            print(transaction_to_be_updated.transaction_status)
                            transaction_to_be_updated.transaction_status = "Completed"
                            transaction_to_be_updated.save()
                            print(user.phone)
                            print("***********")
                            receiver_message = f"Your bundle purchase has been completed successfully. {bundle}MB has been credited to you by {user.phone}.\nReference: {reference}\n"
                            sms_message = f"Hello @{user.username}. Your bundle purchase has been completed successfully. {bundle}MB has been credited to {receiver}.\nReference: {reference}\nThank you for using Noble Data GH.\n\nThe Noble Data GH"

                            num_without_0 = receiver[1:]
                            print(num_without_0)
                            receiver_body = {
                                'recipient': f"233{num_without_0}",
                                'sender_id': 'Noble Data',
                                'message': receiver_message
                            }

                            response = requests.request('POST', url=sms_url, params=receiver_body, headers=sms_headers)
                            print(response.text)

                            sms_body = {
                                'recipient': f"233{user.phone}",
                                'sender_id': 'Noble Data',
                                'message': sms_message
                            }

                            response = requests.request('POST', url=sms_url, params=sms_body, headers=sms_headers)

                            print(response.text)

                            return HttpResponse(status=200)
                        else:
                            transaction_to_be_updated = models.IShareBundleTransaction.objects.get(
                                reference=reference)
                            transaction_to_be_updated.transaction_status = "Failed"
                            new_transaction.save()
                            sms_message = f"Hello @{user.username}. Something went wrong with your transaction. Contact us for enquiries.\nBundle: {bundle}MB\nPhone Number: {receiver}.\nReference: {reference}\nThank you for using Noble Data GH.\n\nThe Noble Data GH"

                            sms_body = {
                                'recipient': f"233{user.phone}",
                                'sender_id': 'Noble Data',
                                'message': sms_message
                            }
                            response = requests.request('POST', url=sms_url, params=sms_body, headers=sms_headers)
                            print(response.text)
                            return HttpResponse(status=500)
                    else:
                        transaction_to_be_updated = models.IShareBundleTransaction.objects.get(
                            reference=reference)
                        transaction_to_be_updated.transaction_status = "Failed"
                        new_transaction.save()
                        sms_message = f"Hello @{request.user.username}. Something went wrong with your transaction. Contact us for enquiries.\nBundle: {bundle}MB\nPhone Number: {receiver}.\nReference: {reference}\nThank you for using Noble Data GH.\n\nThe Noble Data GH"

                        sms_body = {
                            'recipient': f'233{user.phone}',
                            'sender_id': 'Noble Data',
                            'message': sms_message
                        }

                        response = requests.request('POST', url=sms_url, params=sms_body, headers=sms_headers)

                        print(response.text)
                        return HttpResponse(status=500)
                elif channel == "mtn":
                    user_id = metadata.get('user_id')
                    new_payment = models.Payment.objects.create(
                        user=user,
                        reference=reference,
                        amount=paid_amount,
                        transaction_date=datetime.now(),
                        transaction_status="Completed"
                    )
                    new_payment.save()

                    bundle = models.MTNBundlePrice.objects.get(price=float(
                        real_amount)).bundle_volume if user.status == "User" else models.AgentMTNBundlePrice.objects.get(
                        price=float(real_amount)).bundle_volume

                    url = "https://posapi.bestpaygh.com/api/v1/initiate_mtn_transaction"

                    payload = json.dumps({
                        "user_id": user_id,
                        "receiver": receiver,
                        "data_volume": bundle,
                        "reference": reference,
                        "amount": real_amount,
                        "channel": user.phone
                    })
                    headers = {
                        'Authorization': config("AT"),
                        'Content-Type': 'application/json'
                    }

                    response = requests.request("POST", url, headers=headers, data=payload)

                    print(response.text)

                    print(receiver)

                    new_mtn_transaction = models.MTNTransaction.objects.create(
                        user=user,
                        bundle_number=receiver,
                        offer=f"{bundle}MB",
                        reference=reference,
                    )
                    new_mtn_transaction.save()
                    return HttpResponse(status=200)
                else:
                    return HttpResponse(status=200)
            else:
                return HttpResponse(status=200)
        else:
            return HttpResponse(status=401)


@login_required(login_url='login')
def history(request):
    user_transactions = models.IShareBundleTransaction.objects.filter(user=request.user).order_by('transaction_date').reverse()
    header = "AirtelTigo Transactions"
    net = "tigo"
    context = {'txns': user_transactions, "header": header, "net": net}
    return render(request, "layouts/history.html", context=context)


@login_required(login_url='login')
def mtn_history(request):
    user_transactions = models.MTNTransaction.objects.filter(user=request.user).order_by('transaction_date').reverse()
    header = "MTN Transactions"
    net = "mtn"
    context = {'txns': user_transactions, "header": header, "net": net}
    return render(request, "layouts/history.html", context=context)


def verify_transaction(request, reference):
    if request.method == "GET":
        response = helper.verify_paystack_transaction(reference)
        data = response.json()
        try:
            status = data["data"]["status"]
            amount = data["data"]["amount"]
            api_reference = data["data"]["reference"]
            date = data["data"]["paid_at"]
            real_amount = float(amount)/100
            print(status)
            print(real_amount)
            print(api_reference)
            print(reference)
            print(date)
        except:
            status = data["status"]
        return JsonResponse({'status': status})


@login_required(login_url='login')
def admin_mtn_history(request):
    if request.user.is_staff and request.user.is_superuser:
        all_txns = models.MTNTransaction.objects.all().order_by('transaction_date').reverse()
        context = {'txns': all_txns}
        return render(request, "layouts/services/mtn_admin.html", context=context)


@login_required(login_url='login')
def mark_as_sent(request, pk):
    if request.user.is_staff and request.user.is_superuser:
        txn = models.MTNTransaction.objects.filter(id=pk).first()
        print(txn)
        txn.transaction_status = "Completed"
        txn.save()
        sms_headers = {
            'Authorization': 'Bearer 1050|VDqcCUHwCBEbjcMk32cbdOhCFlavpDhy6vfgM4jU',
            'Content-Type': 'application/json'
        }

        sms_url = 'https://webapp.usmsgh.com/api/sms/send'
        sms_message = f"Your account has been credited with {txn.offer}.\nTransaction Reference: {txn.reference}"

        sms_body = {
            'recipient': f"233{txn.bundle_number}",
            'sender_id': 'Noble Data',
            'message': sms_message
        }
        response = requests.request('POST', url=sms_url, params=sms_body, headers=sms_headers)
        print(response.text)
        return redirect('mtn_admin')


def credit_user(request):
    form = forms.CreditUserForm()
    if request.user.is_superuser:
        if request.method == "POST":
            form = forms.CreditUserForm(request.POST)
            if form.is_valid():
                user = form.cleaned_data["user"]
                amount = form.cleaned_data["amount"]
                print(user)
                print(amount)
                user_needed = models.CustomUser.objects.get(username=user)
                if user_needed.wallet is None:
                    user_needed.wallet = float(amount)
                else:
                    user_needed.wallet += float(amount)
                user_needed.save()
                print(user_needed.username)
                messages.success(request, "Crediting Successful")
                return redirect('credit_user')
        context = {'form': form}
        return render(request, "layouts/services/credit.html", context=context)
    else:
        messages.error(request, "Access Denied")
        return redirect('home')


@login_required(login_url='login')
def topup_info(request):
    if request.method == "POST":
        admin = models.AdminInfo.objects.filter().first().phone_number
        user = models.CustomUser.objects.get(id=request.user.id)
        amount = request.POST.get("amount")
        print(amount)
        reference = helper.top_up_ref_generator()
        new_topup_request = models.TopUpRequest.objects.create(
            user=request.user,
            amount=amount,
            reference=reference,
        )
        new_topup_request.save()

        sms_headers = {
            'Authorization': 'Bearer 1050|VDqcCUHwCBEbjcMk32cbdOhCFlavpDhy6vfgM4jU',
            'Content-Type': 'application/json'
        }

        sms_url = 'https://webapp.usmsgh.com/api/sms/send'
        sms_message = f"A top up request has been placed.\nGHS{amount} for {user}.\nReference: {reference}"

        sms_body = {
            'recipient': f"233{admin}",
            'sender_id': 'Noble Data',
            'message': sms_message
        }
        try:
            response = requests.request('POST', url=sms_url, params=sms_body, headers=sms_headers)
            print(response.text)
        except:
            pass
        messages.success(request, f"Your Request has been sent successfully. Kindly go on to pay to {admin} and use the reference stated as reference. Reference: {reference}")
        return redirect("request_successful", reference)
    return render(request, "layouts/topup-info.html")


@login_required(login_url='login')
def request_successful(request, reference):
    admin = models.AdminInfo.objects.filter().first()
    context = {
        "name": admin.name,
        "number": f"0{admin.momo_number}",
        "channel": admin.payment_channel,
        "reference": reference
    }
    return render(request, "layouts/services/request_successful.html", context=context)


def topup_list(request):
    if request.user.is_superuser:
        topup_requests = models.TopUpRequest.objects.all().order_by('date').reverse()
        context = {
            'requests': topup_requests,
        }
        return render(request, "layouts/services/topup_list.html", context=context)
    else:
        messages.error(request, "Access Denied")
        return redirect('home')


@login_required(login_url='login')
def credit_user_from_list(request, reference):
    if request.user.is_superuser:
        crediting = models.TopUpRequest.objects.filter(reference=reference).first()
        user = crediting.user
        custom_user = models.CustomUser.objects.get(username=user.username)
        if crediting.status:
            return redirect('topup_list')
        amount = crediting.amount
        print(user)
        print(user.phone)
        print(amount)
        custom_user.wallet += amount
        custom_user.save()
        crediting.status = True
        crediting.credited_at = datetime.now()
        crediting.save()
        sms_headers = {
            'Authorization': 'Bearer 1050|VDqcCUHwCBEbjcMk32cbdOhCFlavpDhy6vfgM4jU',
            'Content-Type': 'application/json'
        }

        sms_url = 'https://webapp.usmsgh.com/api/sms/send'
        sms_message = f"Hello,\nYour wallet has been topped up with GHS{amount}.\nReference: {reference}.\nThank you"

        sms_body = {
            'recipient': f"233{custom_user.phone}",
            'sender_id': 'Noble Data',
            'message': sms_message
        }
        try:
            response = requests.request('POST', url=sms_url, params=sms_body, headers=sms_headers)
            print(response.text)
        except:
            pass

        messages.success(request, f"{user} has been credited with {amount}")
        return redirect('topup_list')




