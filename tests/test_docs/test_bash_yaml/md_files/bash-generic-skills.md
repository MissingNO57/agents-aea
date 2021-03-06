``` bash
aea fetch fetchai/generic_seller:0.5.0 --alias my_seller_aea
cd my_seller_aea
aea install
```
``` bash
aea create my_seller_aea
cd my_seller_aea
aea add connection fetchai/p2p_libp2p:0.5.0
aea add connection fetchai/soef:0.5.0
aea add connection fetchai/ledger:0.2.0
aea add skill fetchai/generic_seller:0.8.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.5.0
```
``` bash
aea fetch fetchai/generic_buyer:0.5.0 --alias my_buyer_aea
cd my_buyer_aea
aea install
```
``` bash
aea create my_buyer_aea
cd my_buyer_aea
aea add connection fetchai/p2p_libp2p:0.5.0
aea add connection fetchai/soef:0.5.0
aea add connection fetchai/ledger:0.2.0
aea add skill fetchai/generic_buyer:0.7.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.5.0
```
``` bash
aea generate-key cosmos
aea add-key cosmos cosmos_private_key.txt
aea add-key cosmos cosmos_private_key.txt --connection
```
``` bash
aea generate-key cosmos
aea add-key cosmos cosmos_private_key.txt
aea add-key cosmos cosmos_private_key.txt --connection
```
``` bash
aea generate-wealth cosmos
```
``` bash
cd my_seller_aea
aea config set vendor.fetchai.skills.generic_seller.is_abstract false --type bool
```
``` bash
cd my_buyer_aea
aea config set vendor.fetchai.skills.generic_buyer.is_abstract false --type bool
```
``` bash
aea run
```
``` bash
aea run
```
``` bash
cd ..
aea delete my_seller_aea
aea delete my_buyer_aea
```
``` yaml
default_routing:
  fetchai/ledger_api:0.1.0: fetchai/ledger:0.2.0
  fetchai/oef_search:0.3.0: fetchai/soef:0.5.0
```
``` yaml
default_routing:
  fetchai/ledger_api:0.1.0: fetchai/ledger:0.2.0
  fetchai/oef_search:0.3.0: fetchai/soef:0.5.0
```
``` yaml
models:
  ...
  strategy:
    args:
      currency_id: FET
      data_for_sale:
        generic: data
      has_data_source: false
      is_ledger_tx: true
      ledger_id: cosmos
      location:
        latitude: 0.127
        longitude: 51.5194
      service_data:
        key: seller_service
        value: generic_service
      service_id: generic_service
      unit_price: 10
    class_name: GenericStrategy
```
``` yaml
models:
  ...
  strategy:
    args:
      currency_id: FET
      is_ledger_tx: true
      ledger_id: cosmos
      location:
        latitude: 0.127
        longitude: 51.5194
      max_negotiations: 1
      max_tx_fee: 1
      max_unit_price: 20
      search_query:
        constraint_type: ==
        search_key: seller_service
        search_value: generic_service
      search_radius: 5.0
      service_id: generic_service
    class_name: GenericStrategy
```
``` yaml
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers: ['SOME_ADDRESS']
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```
