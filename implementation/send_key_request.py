import json
import base64
from algosdk.v2client import algod
from algosdk import mnemonic, account
from algosdk.future.transaction import PaymentTxn
from decouple import config
import time

app_id_box = config('APPLICATION_ID_BOX')
authority1_address = config('AUTHORITY1_ADDRESS')
authority2_address = config('AUTHORITY2_ADDRESS')
authority3_address = config('AUTHORITY3_ADDRESS')
authority4_address = config('AUTHORITY4_ADDRESS')

manufacturer_private_key = config('READER_PRIVATEKEY_MANUFACTURER')
electronics_private_key = config('READER_PRIVATEKEY_SUPPLIER1')
mechanics_private_key = config('READER_PRIVATEKEY_SUPPLIER2')

# creator_mnemonic = "work dad crazy similar average cover reward account car first taxi glide pluck key digital provide able suspect undo company van what emerge ability pass"
algod_address = "https://testnet-algorand.api.purestake.io/ps2"
algod_token = "p8IwM35NPv3nRf0LLEquJ5tmpOtcC4he7KKnJ3wE"
headers = {
    "X-API-Key": algod_token,
}

creator_private_key = electronics_private_key


def get_private_key_from_mnemonic(mn):
    private_key = mnemonic.to_private_key(mn)
    return private_key


# utility for waiting on a transaction confirmation
def wait_for_confirmation(client, transaction_id, timeout):
    """
    Wait until the transaction is confirmed or rejected, or until 'timeout'
    number of rounds have passed.
    Args:
        transaction_id (str): the transaction to wait for
        timeout (int): maximum number of rounds to wait
    Returns:
        dict: pending transaction information, or throws an error if the transaction
            is not confirmed or rejected in the next timeout rounds
    """
    start_round = client.status()["last-round"] + 1;
    current_round = start_round

    while current_round < start_round + timeout:
        try:
            pending_txn = client.pending_transaction_info(transaction_id)
        except Exception:
            return
        if pending_txn.get("confirmed-round", 0) > 0:
            return pending_txn
        elif pending_txn["pool-error"]:
            raise Exception(
                'pool error: {}'.format(pending_txn["pool-error"]))
        client.status_after_block(current_round)
        current_round += 1
    raise Exception(
        'pending tx not found in timeout rounds, timeout value = : {}'.format(timeout))


def send_key_request():
    # start = time.time()
    algod_client = algod.AlgodClient(algod_token, algod_address, headers)

    # private_key = get_private_key_from_mnemonic(creator_mnemonic)
    private_key = creator_private_key
    my_address = account.address_from_private_key(private_key)
    print("My address: {}".format(my_address))
    params = algod_client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    # params.flat_fee = True
    # params.fee = 1000
    note = 'generate your part of my key,bob,' + str(app_id_box)
    note_encoded = note.encode()
    receiver = authority4_address

    unsigned_txn = PaymentTxn(my_address, params, receiver, 0, None, note_encoded)

    # sign transaction
    signed_txn = unsigned_txn.sign(private_key)
    generate_transaction = time.time()

    # send transaction
    txid = algod_client.send_transaction(signed_txn)
    # blockchain_execution_sending = time.time()
    print("Send transaction with txID: {}".format(txid))

    # # wait for confirmation
    try:
        confirmed_txn = wait_for_confirmation(algod_client, txid, 4)
    except Exception as err:
        print(err)
        return
    # blockchain_execution_confirmation = time.time()

    # print('The time for transaction generation is :', (generate_transaction - start) * 10 ** 3, 'ms')
    # print('The time for blockchain sending is :', (blockchain_execution_sending - generate_transaction) * 10 ** 3, 'ms')
    # print('The time for blockchain confirmation is :', (blockchain_execution_confirmation - blockchain_execution_sending
    #                                                     ) * 10 ** 3, 'ms')
    # print('The time for blockchain execution is :', (blockchain_execution_sending - start) * 10 ** 3, 'ms')
    # print('The time for blockchain execution total is :', (blockchain_execution_confirmation - start) * 10 ** 3, 'ms')


if __name__ == "__main__":
    send_key_request()
