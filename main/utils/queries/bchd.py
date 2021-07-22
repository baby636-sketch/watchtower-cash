#!/usr/bin/env python3
import grpc
import random
import logging
from main.utils.bchd import bchrpc_pb2 as pb
from main.utils.bchd import bchrpc_pb2_grpc as bchrpc
import base64

LOGGER = logging.getLogger(__name__)

class BCHDQuery(object):

    def __init__(self):
        nodes = [
            'bchd.imaginary.cash:8335',
            'bchd.greyh.at:8335',
            'bchd.fountainhead.cash:443'
        ]
        self.base_url = random.choice(nodes)

        self._slp_action = {
            0: 'NON_SLP',
            1: 'NON_SLP_BURN',
            2: 'SLP_PARSE_ERROR',
            3: 'SLP_UNSUPPORTED_VERSION',
            4: 'SLP_V1_GENESIS',
            5: 'SLP_V1_MINT',
            6: 'SLP_V1_SEND',
            7: 'SLP_V1_NFT1_GROUP_GENESIS',
            8: 'SLP_V1_NFT1_GROUP_MINT',
            9: 'SLP_V1_NFT1_GROUP_SEND',
            10: 'SLP_V1_NFT1_UNIQUE_CHILD_GENESIS',
            11: 'SLP_V1_NFT1_UNIQUE_CHILD_SEND'
        }

    def get_latest_block(self):
        creds = grpc.ssl_channel_credentials()

        with grpc.secure_channel(self.base_url, creds) as channel:
            stub = bchrpc.bchrpcStub(channel)
            
            req = pb.GetBlockchainInfoRequest()
            resp = stub.GetBlockchainInfo(req)
            latest_block = resp.best_height

            req = pb.GetBlockRequest()
            req.height = latest_block
            req.full_transactions = False
            resp = stub.GetBlock(req)

            return latest_block, resp.block.transaction_data

    def _parse_transaction(self, txn, parse_slp=False):
        tx_hash = bytearray(txn.hash[::-1]).hex()
        transaction = {
            'txid': tx_hash,
            'valid': True
        }
        total_input_sats = 0
        total_output_sats = 0
        if parse_slp:
            is_valid = bool(txn.slp_transaction_info.validity_judgement)
            transaction['valid'] = is_valid
            transaction['token_id'] = txn.slp_transaction_info.token_id.hex()
            slp_action = txn.slp_transaction_info.slp_action
            transaction['slp_action'] = self._slp_action[slp_action]

            # If genesis tx, give more token metadata
            genesis_map = {
                4: 'v1_genesis',
                7: 'v1_genesis',
                10: 'nft1_child_genesis'
            }
            if slp_action in genesis_map.keys():
                genesis_info = eval('txn.slp_transaction_info.' + genesis_map[slp_action])
                token_type = txn.outputs[1].slp_token.token_type
                parent_group = None
                if token_type == 65:
                    parent_group = genesis_info.group_token_id.hex()
                transaction['token_info'] = {
                    'name': genesis_info.name.decode(),
                    'type': token_type,
                    'ticker': genesis_info.ticker.decode(),
                    'nft_token_group': parent_group,
                    'decimals': genesis_info.decimals or 0
                }
            
            transaction['inputs'] = []
            if is_valid:
                transaction['token_id'] = txn.slp_transaction_info.token_id.hex()
                for tx_input in txn.inputs:
                    if tx_input.slp_token.token_id:
                        input_txid = tx_input.outpoint.hash[::-1].hex()
                        decimals = tx_input.slp_token.decimals or 0
                        amount = tx_input.slp_token.amount / (10 ** decimals)
                        data = {
                            'txid': input_txid,
                            'spent_index': tx_input.outpoint.index,
                            'amount': amount,
                            'address': 'simpleledger:' + tx_input.slp_token.address
                        }
                        transaction['inputs'].append(data)
                transaction['outputs'] = []
                output_index = 0
                for tx_output in txn.outputs:
                    total_output_sats += tx_output.value
                    if tx_output.slp_token.token_id:
                        decimals = tx_output.slp_token.decimals or 0
                        amount = tx_output.slp_token.amount / (10 ** decimals)
                        data = {
                            'address': 'simpleledger:' + tx_output.slp_token.address,
                            'amount': amount,
                            'index': output_index
                        }
                        transaction['outputs'].append(data)
                    output_index += 1

            # Valid or invalid, parse the inputs for marking of spent UTXOs and computation of tx fee
            for tx_input in txn.inputs:
                total_input_sats += tx_input.value
                input_txid = tx_input.outpoint.hash[::-1].hex()
                data = {
                    'txid': input_txid,
                    'spent_index': tx_input.outpoint.index,
                    'value': tx_input.value,
                    'address': 'bitcoincash:' + tx_input.address
                }
                transaction['inputs'].append(data)
        else:
            transaction['inputs'] = []
            for tx_input in txn.inputs:
                total_input_sats += tx_input.value
                input_txid = tx_input.outpoint.hash[::-1].hex()
                data = {
                    'txid': input_txid,
                    'spent_index': tx_input.outpoint.index,
                    'value': tx_input.value,
                    'address': 'bitcoincash:' + tx_input.address
                }
                transaction['inputs'].append(data)
            transaction['outputs'] = []
            output_index = 0
            for tx_output in txn.outputs:
                if tx_output.value is not None:
                    total_output_sats += tx_output.value
                if tx_output.address and tx_output.value:
                    data = {
                        'address': 'bitcoincash:' + tx_output.address,
                        'value': tx_output.value,
                        'index': output_index
                    }
                    transaction['outputs'].append(data)
                output_index += 1

        transaction['tx_fee'] =  total_input_sats - total_output_sats
        return transaction

    def get_transaction(self, transaction_hash, parse_slp=False):
        creds = grpc.ssl_channel_credentials()

        with grpc.secure_channel(self.base_url, creds) as channel:
            stub = bchrpc.bchrpcStub(channel)

            req = pb.GetTransactionRequest()
            txn_bytes = bytes.fromhex(transaction_hash)[::-1]
            req.hash = txn_bytes
            req.include_token_metadata = True

            resp = stub.GetTransaction(req)
            txn = resp.transaction
            print(txn)
            return self._parse_transaction(txn, parse_slp=parse_slp)

    def get_utxos(self, address):
        creds = grpc.ssl_channel_credentials()

        with grpc.secure_channel(self.base_url, creds) as channel:
            stub = bchrpc.bchrpcStub(channel)

            req = pb.GetAddressUnspentOutputsRequest()
            req.address = address
            req.include_mempool = True
            resp = stub.GetAddressUnspentOutputs(req)
            return resp.outputs

    def get_transactions_count(self, blockheight):
        creds = grpc.ssl_channel_credentials()

        with grpc.secure_channel(self.base_url, creds) as channel:
            stub = bchrpc.bchrpcStub(channel)

            req = pb.GetBlockRequest()
            req.height = blockheight
            req.full_transactions = False
            resp = stub.GetBlock(req)

            trs = resp.block.transaction_data
            return len(trs)

    def broadcast_transaction(self, transaction):
        txn_bytes = bytes.fromhex(transaction)
        creds = grpc.ssl_channel_credentials()

        with grpc.secure_channel(self.base_url, creds) as channel:
            stub = bchrpc.bchrpcStub(channel)

            req = pb.SubmitTransactionRequest()
            req.transaction = txn_bytes
            resp = stub.SubmitTransaction(req)

            tx_hash = bytearray(resp.hash[::-1]).hex()
            return tx_hash
