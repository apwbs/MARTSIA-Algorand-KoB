from algosdk.v2client import indexer
import base64
import time
from decouple import config
import authority1_keygeneration
import rsa
import json
import retriever
from algosdk.v2client import algod
from algosdk import mnemonic, account
from algosdk.future.transaction import PaymentTxn
import ipfshttpclient
import io
import sqlite3

api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
app_id_pk_readers = config('APPLICATION_ID_PK_READERS')

authority1_address = config('AUTHORITY1_ADDRESS')
authority1_mnemonic = config('AUTHORITY1_MNEMONIC')

indexer_address = "https://testnet-algorand.api.purestake.io/idx2"
indexer_token = ""
headers = {
    "X-API-Key": "p8IwM35NPv3nRf0LLEquJ5tmpOtcC4he7KKnJ3wE"
}

indexer_client = indexer.IndexerClient(indexer_token, indexer_address, headers)

algod_address = "https://testnet-algorand.api.purestake.io/ps2"
algod_token = "p8IwM35NPv3nRf0LLEquJ5tmpOtcC4he7KKnJ3wE"
headers = {
    "X-API-Key": algod_token,
}

start = 0
creator_mnemonic = authority1_mnemonic


def get_private_key_from_mnemonic(mn):
    private_key = mnemonic.to_private_key(mn)
    return private_key


def send_ipfs_link(reader_address, process_instance_id, hash_file):
    algod_client = algod.AlgodClient(algod_token, algod_address, headers)

    private_key = get_private_key_from_mnemonic(creator_mnemonic)
    my_address = account.address_from_private_key(private_key)
    print("My address: {}".format(my_address))
    params = algod_client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    # params.flat_fee = True
    # params.fee = 1000
    note = hash_file + ',' + str(process_instance_id)
    note_encoded = note.encode()
    receiver = reader_address

    unsigned_txn = PaymentTxn(my_address, params, receiver, 0, None, note_encoded)

    # sign transaction
    signed_txn = unsigned_txn.sign(private_key)

    # send transaction
    # end_off_chain = time.time()
    txid = algod_client.send_transaction(signed_txn)
    # blockchain_execution = time.time()
    print("Send transaction with txID: {}".format(txid))
    # print('The time for transaction generation is :', (end_off_chain - start) * 10 ** 3, 'ms')
    # print('The time for blockchain execution is :', (blockchain_execution - end_off_chain) * 10 ** 3, 'ms')


def generate_key(x):
    gid = base64.b64decode(x['note']).decode('utf-8').split(',')[1]
    process_instance_id = int(base64.b64decode(x['note']).decode('utf-8').split(',')[2])
    reader_address = x['sender']
    key = authority1_keygeneration.generate_user_key(gid, process_instance_id, reader_address)
    cipher_generated_key(reader_address, process_instance_id, key)


def cipher_generated_key(reader_address, process_instance_id, generated_ma_key):
    public_key_ipfs_link = retriever.retrieveReaderPublicKey(app_id_pk_readers, reader_address)
    getfile = api.cat(public_key_ipfs_link)
    getfile = getfile.split(b'###')
    if getfile[0].split(b': ')[1].decode('utf-8') == reader_address:
        publicKey_usable = rsa.PublicKey.load_pkcs1(getfile[1].rstrip(b'"').replace(b'\\n', b'\n'))

        info = [generated_ma_key[i:i + 117] for i in range(0, len(generated_ma_key), 117)]

        f = io.BytesIO()
        for part in info:
            crypto = rsa.encrypt(part, publicKey_usable)
            f.write(crypto)
        f.seek(0)

        file_to_str = f.read()
        j = base64.b64encode(file_to_str).decode('ascii')
        s = json.dumps(j)
        hash_file = api.add_json(s)
        print(hash_file)

        # name_file = 'files/keys_readers/generated_key_ciphered_' + str(reader_address) + '_' \
        #             + str(process_instance_id) + '.txt'
        # for part in info:
        #     crypto = rsa.encrypt(part, publicKey_usable)
        #     with open(name_file, 'ab') as ipfs:
        #         ipfs.write(crypto)
        #         print(len(crypto))
        # new_file = api.add(name_file)
        # hash_file = new_file['Hash']
        # print(f'ipfs hash: {hash_file}')
        # exit()

        send_ipfs_link(reader_address, process_instance_id, hash_file)


def transactions_monitoring():
    # global start
    # start = time.time()
    min_round = 33258687
    transactions = []
    note = 'generate your part of my key'
    while True:
        response = indexer_client.search_transactions_by_address(address=authority1_address, min_round=min_round,
                                                                 txn_type='pay', max_amount=0)
        for tx in response['transactions']:
            if tx['id'] not in transactions and 'note' in tx:
                if base64.b64decode(tx['note']).decode('utf-8').split(',')[0] == note:
                    transactions.append(tx)
        min_round = min_round + 1
        for x in transactions:
            generate_key(x)
            transactions.remove(x)
        time.sleep(5)


if __name__ == "__main__":
    transactions_monitoring()
