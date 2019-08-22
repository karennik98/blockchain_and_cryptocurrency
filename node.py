from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from wallet import Wallet
from blockchain import Blockchain


app = Flask(__name__)
CORS(app)


@app.route('/', methods=['GET'])
def get_node_ui():
    return send_from_directory('ui', 'node.html')


@app.route('/network', methods=['GET'])
def get_network_ui():
    return send_from_directory('ui', 'network.html')


@app.route('/wallet', methods=['POST'])
def create_keys():
    wallet.create_keys()
    if wallet.save_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key, port)
        responce = {
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'funds': blockchain.get_balance()
        }
        return jsonify(responce), 201
    else:
        responce= {
            'message':'Saving the keys failed.'
        }
        return jsonify(responce), 500


@app.route('/wallet', methods=['GET'])
def load_keys():
    if wallet.load_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key, port)
        responce = {
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'funds': blockchain.get_balance()
        }
        return jsonify(responce), 201
    else:
        responce= {
            'message':'Loading the keys failed.'
        }
        return jsonify(responce), 500


@app.route('/balance', methods=['GET'])
def get_balance():
    balance = blockchain.get_balance()
    if balance != None:
        responce = {
            'message': 'Fetched balance seccessfully.',
            'funds': balance
        }
        return jsonify(responce), 201
    else:
        responce = {
            'message': 'Loading balance faild.',
            'wallet_set_up': wallet.public_key != None
        }
        return jsonify(responce), 500



@app.route('/transaction', methods=['POST'])
def add_transaction():
    if wallet.public_key == None:
        responce = {
            'messaage': 'No wallet set up.'
        }
        return jsonify(responce), 400
    
    values = request.get_json()
    if not values:
        responce = {
            'message': 'No data found.' 
        }
        return jsonify(responce), 400
    
    required_fields = ['recipient', 'amount']
    if not all(field in values for field in required_fields):
        responce = {
            'message': 'Required data is missing.'
        }
        return jsonify(responce), 400
    
    recipient = values['recipient']
    amount = values['amount']
    
    signature = wallet.sign_transaction(wallet.public_key, recipient, amount)
    success = blockchain.add_transaction(recipient, wallet.public_key, signature, amount)
    if success:
        responce = {
            'message': 'Successfully added transaction.',
            'transaction': {
                'sender': wallet.public_key,
                'recipient': recipient,
                'amount': amount,
                'signature': signature
            },
            'funds': blockchain.get_balance()
        }
        return jsonify(responce), 201
    else:
        responce = {
            'message': 'Creating a transaction failed.'
        }
        return jsonify(responce), 500

@app.route('/mine', methods=['POST'])
def mine():
    block = blockchain.mine_block()
    if block != None:
        dict_block = block.__dict__.copy()
        dict_block['transactions'] = [tx.__dict__ for tx in dict_block['transactions']]
        responce = {
            'message': 'Block added successfully.',
            'block': dict_block,
            'funds': blockchain.get_balance()
        }
        return jsonify(responce), 201
    else:
        responce = {
            'message': 'Adding a block faild.',
            'wallet_set_up': wallet.public_key != None
        }
        return jsonify(responce), 500
    
    
@app.route('/transactions', methods=['GET'])
def get_open_transactions():
    transactions = blockchain.get_open_transactions()
    dict_transactions = [tx.__dict__ for tx in transactions]
    return jsonify(dict_transactions), 200

@app.route('/chain', methods=['GET'])
def get_chain():
    chain_snpashot = blockchain.chain
    dict_chain = [block.__dict__.copy() for block in chain_snpashot]
    for dict_block in dict_chain:
        dict_block['transactions'] = [tx.__dict__ for tx in dict_block['transactions']]
    return jsonify(dict_chain), 200


@app.route('/node', methods=['POST'])
def add_node():
    values = request.get_json()
    if not values:
        response = {
            'message': 'No data attached.'
        }
        return jsonify(response), 400
    if 'node' not in values:
        response = {
            'message': 'No node data founnd.'
        }
        return jsonify(response), 400
    node = values['node']
    blockchain.add_peer_node(node)
    response = {
        'message': 'Node added successfully.',
        'all_nodes': list(blockchain.get_peer_nodes())
    }
    return jsonify(response), 201


@app.route('/node/<node_url>', methods=['DELETE'])
def remove_node(node_url):
    if node_url == '' or node_url == None:
        responce = {
            'message': 'No node found.'
        }
        return jsonify(responce), 400
    blockchain.remove_peer_node(node_url)
    responce = {
        'message': 'Node removed.',
        'all_nodes': blockchain.get_peer_nodes()
    }    
    return jsonify(responce), 200


@app.route('/nodes', methods=['GET'])
def get_nodes():
    nodes = blockchain.get_peer_nodes()
    response = {
        'all_nodes': nodes
    }
    return jsonify(response), 200

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=5000)
    args = parser.parse_args()
    port = args.port
    wallet = Wallet(port)
    blockchain = Blockchain(wallet.public_key, port)
    app.run(host='0.0.0.0', port=port)