# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""This package contains handlers for the erc1155-client skill."""

from typing import Optional, cast

from aea.configurations.base import ProtocolId
from aea.helpers.transaction.base import RawMessage, Terms
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.signing.message import SigningMessage
from aea.skills.base import Handler

from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.erc1155_client.dialogues import (
    ContractApiDialogue,
    ContractApiDialogues,
    DefaultDialogues,
    FipaDialogue,
    FipaDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    OefSearchDialogue,
    OefSearchDialogues,
    SigningDialogue,
    SigningDialogues,
)
from packages.fetchai.skills.erc1155_client.strategy import Strategy

LEDGER_API_ADDRESS = "fetchai/ledger:0.2.0"


class FipaHandler(Handler):
    """This class implements a FIPA handler."""

    SUPPORTED_PROTOCOL = FipaMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        fipa_msg = cast(FipaMessage, message)

        # recover dialogue
        fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
        fipa_dialogue = cast(FipaDialogue, fipa_dialogues.update(fipa_msg))
        if fipa_dialogue is None:
            self._handle_unidentified_dialogue(fipa_msg)
            return

        # handle message
        if fipa_msg.performative == FipaMessage.Performative.PROPOSE:
            self._handle_propose(fipa_msg, fipa_dialogue)
        else:
            self._handle_invalid(fipa_msg, fipa_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, fipa_msg: FipaMessage) -> None:
        """
        Handle an unidentified dialogue.

        Respond to the sender with a default message containing the appropriate error information.

        :param fipa_msg: the message
        :return: None
        """
        self.context.logger.info(
            "[{}]: unidentified dialogue.".format(self.context.agent_name)
        )
        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)
        default_msg = DefaultMessage(
            performative=DefaultMessage.Performative.ERROR,
            dialogue_reference=default_dialogues.new_self_initiated_dialogue_reference(),
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"fipa_message": fipa_msg.encode()},
        )
        default_msg.counterparty = fipa_msg.counterparty
        default_dialogues.update(default_msg)
        self.context.outbox.put_message(message=default_msg)

    def _handle_propose(
        self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue
    ) -> None:
        """
        Handle the CFP.

        If the CFP matches the supplied services then send a PROPOSE, otherwise send a DECLINE.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
        :return: None
        """
        if all(
            key
            in [
                "contract_address",
                "from_supply",
                "to_supply",
                "value",
                "trade_nonce",
                "token_id",
            ]
            for key in fipa_msg.proposal.values.keys()
        ):
            # accept any proposal with the correct keys
            self.context.logger.info(
                "[{}]: received valid PROPOSE from sender={}: proposal={}".format(
                    self.context.agent_name,
                    fipa_msg.counterparty[-5:],
                    fipa_msg.proposal.values,
                )
            )
            strategy = cast(Strategy, self.context.strategy)
            contract_api_dialogues = cast(
                ContractApiDialogues, self.context.contract_api_dialogues
            )
            contract_api_msg = ContractApiMessage(
                performative=ContractApiMessage.Performative.GET_RAW_MESSAGE,
                dialogue_reference=contract_api_dialogues.new_self_initiated_dialogue_reference(),
                ledger_id=strategy.ledger_id,
                contract_id="fetchai/erc1155:0.6.0",
                contract_address=fipa_msg.proposal.values["contract_address"],
                callable="get_hash_single",
                kwargs=ContractApiMessage.Kwargs(
                    {
                        "from_address": fipa_msg.counterparty,
                        "to_address": self.context.agent_address,
                        "token_id": int(fipa_msg.proposal.values["token_id"]),
                        "from_supply": int(fipa_msg.proposal.values["from_supply"]),
                        "to_supply": int(fipa_msg.proposal.values["to_supply"]),
                        "value": int(fipa_msg.proposal.values["value"]),
                        "trade_nonce": int(fipa_msg.proposal.values["trade_nonce"]),
                    }
                ),
            )
            terms = Terms(
                ledger_id=strategy.ledger_id,
                sender_address=self.context.agent_address,
                counterparty_address=fipa_msg.counterparty,
                amount_by_currency_id={},
                quantities_by_good_id={
                    str(fipa_msg.proposal.values["token_id"]): int(
                        fipa_msg.proposal.values["from_supply"]
                    )
                    - int(fipa_msg.proposal.values["to_supply"])
                },
                is_sender_payable_tx_fee=False,
                nonce=str(fipa_msg.proposal.values["trade_nonce"]),
            )
            contract_api_msg.counterparty = LEDGER_API_ADDRESS
            contract_api_dialogue = cast(
                Optional[ContractApiDialogue],
                contract_api_dialogues.update(contract_api_msg),
            )
            assert (
                contract_api_dialogue is not None
            ), "Error when creating contract api dialogue."
            contract_api_dialogue.terms = terms
            contract_api_dialogue.associated_fipa_dialogue = fipa_dialogue
            self.context.outbox.put_message(message=contract_api_msg)
            self.context.logger.info(
                "[{}]: requesting single hash message from contract api...".format(
                    self.context.agent_name
                )
            )
        else:
            self.context.logger.info(
                "[{}]: received invalid PROPOSE from sender={}: proposal={}".format(
                    self.context.agent_name,
                    fipa_msg.counterparty[-5:],
                    fipa_msg.proposal.values,
                )
            )

    def _handle_invalid(
        self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue
    ) -> None:
        """
        Handle a fipa message of invalid performative.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
        :return: None
        """
        self.context.logger.warning(
            "[{}]: cannot handle fipa message of performative={} in dialogue={}.".format(
                self.context.agent_name, fipa_msg.performative, fipa_dialogue
            )
        )


class OefSearchHandler(Handler):
    """This class implements an OEF search handler."""

    SUPPORTED_PROTOCOL = OefSearchMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Call to setup the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        oef_search_msg = cast(OefSearchMessage, message)

        # recover dialogue
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_dialogue = cast(
            Optional[OefSearchDialogue], oef_search_dialogues.update(oef_search_msg)
        )
        if oef_search_dialogue is None:
            self._handle_unidentified_dialogue(oef_search_msg)
            return

        # handle message
        if oef_search_msg.performative is OefSearchMessage.Performative.OEF_ERROR:
            self._handle_error(oef_search_msg, oef_search_dialogue)
        elif oef_search_msg.performative is OefSearchMessage.Performative.SEARCH_RESULT:
            self._handle_search(oef_search_msg, oef_search_dialogue)
        else:
            self._handle_invalid(oef_search_msg, oef_search_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, oef_search_msg: OefSearchMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the message
        """
        self.context.logger.info(
            "[{}]: received invalid oef_search message={}, unidentified dialogue.".format(
                self.context.agent_name, oef_search_msg
            )
        )

    def _handle_error(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        :return: None
        """
        self.context.logger.info(
            "[{}]: received oef_search error message={} in dialogue={}.".format(
                self.context.agent_name, oef_search_msg, oef_search_dialogue
            )
        )

    def _handle_search(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle the search response.

        :param agents: the agents returned by the search
        :return: None
        """
        if len(oef_search_msg.agents) == 0:
            self.context.logger.info(
                "[{}]: found no agents, continue searching.".format(
                    self.context.agent_name
                )
            )
            return

        self.context.logger.info(
            "[{}]: found agents={}, stopping search.".format(
                self.context.agent_name,
                list(map(lambda x: x[-5:], oef_search_msg.agents)),
            )
        )
        strategy = cast(Strategy, self.context.strategy)
        strategy.is_searching = False
        query = strategy.get_service_query()
        fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
        for opponent_address in oef_search_msg.agents:
            cfp_msg = FipaMessage(
                dialogue_reference=fipa_dialogues.new_self_initiated_dialogue_reference(),
                performative=FipaMessage.Performative.CFP,
                query=query,
            )
            cfp_msg.counterparty = opponent_address
            fipa_dialogues.update(cfp_msg)
            self.context.logger.info(
                "[{}]: sending CFP to agent={}".format(
                    self.context.agent_name, opponent_address[-5:]
                )
            )
            self.context.outbox.put_message(message=cfp_msg)

    def _handle_invalid(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        :return: None
        """
        self.context.logger.warning(
            "[{}]: cannot handle oef_search message of performative={} in dialogue={}.".format(
                self.context.agent_name,
                oef_search_msg.performative,
                oef_search_dialogue,
            )
        )


class ContractApiHandler(Handler):
    """Implement the contract api handler."""

    SUPPORTED_PROTOCOL = ContractApiMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        contract_api_msg = cast(ContractApiMessage, message)

        # recover dialogue
        contract_api_dialogues = cast(
            ContractApiDialogues, self.context.contract_api_dialogues
        )
        contract_api_dialogue = cast(
            Optional[ContractApiDialogue],
            contract_api_dialogues.update(contract_api_msg),
        )
        if contract_api_dialogue is None:
            self._handle_unidentified_dialogue(contract_api_msg)
            return

        # handle message
        if contract_api_msg.performative is ContractApiMessage.Performative.RAW_MESSAGE:
            self._handle_raw_message(contract_api_msg, contract_api_dialogue)
        elif contract_api_msg.performative == ContractApiMessage.Performative.ERROR:
            self._handle_error(contract_api_msg, contract_api_dialogue)
        else:
            self._handle_invalid(contract_api_msg, contract_api_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(
        self, contract_api_msg: ContractApiMessage
    ) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the message
        """
        self.context.logger.info(
            "[{}]: received invalid contract_api message={}, unidentified dialogue.".format(
                self.context.agent_name, contract_api_msg
            )
        )

    def _handle_raw_message(
        self,
        contract_api_msg: ContractApiMessage,
        contract_api_dialogue: ContractApiDialogue,
    ) -> None:
        """
        Handle a message of raw_message performative.

        :param contract_api_message: the ledger api message
        :param contract_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(
            "[{}]: received raw message={}".format(
                self.context.agent_name, contract_api_msg
            )
        )
        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        signing_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            dialogue_reference=signing_dialogues.new_self_initiated_dialogue_reference(),
            skill_callback_ids=(str(self.context.skill_id),),
            raw_message=RawMessage(
                contract_api_msg.raw_message.ledger_id,
                contract_api_msg.raw_message.body,
                is_deprecated_mode=True,
            ),
            terms=contract_api_dialogue.terms,
            skill_callback_info={},
        )
        signing_msg.counterparty = "decision_maker"
        signing_dialogue = cast(
            Optional[SigningDialogue], signing_dialogues.update(signing_msg)
        )
        assert signing_dialogue is not None, "Error when creating signing dialogue."
        signing_dialogue.associated_contract_api_dialogue = contract_api_dialogue
        self.context.decision_maker_message_queue.put_nowait(signing_msg)
        self.context.logger.info(
            "[{}]: proposing the transaction to the decision maker. Waiting for confirmation ...".format(
                self.context.agent_name
            )
        )

    def _handle_error(
        self,
        contract_api_msg: ContractApiMessage,
        contract_api_dialogue: ContractApiDialogue,
    ) -> None:
        """
        Handle a message of error performative.

        :param contract_api_message: the ledger api message
        :param contract_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(
            "[{}]: received ledger_api error message={} in dialogue={}.".format(
                self.context.agent_name, contract_api_msg, contract_api_dialogue
            )
        )

    def _handle_invalid(
        self,
        contract_api_msg: ContractApiMessage,
        contract_api_dialogue: ContractApiDialogue,
    ) -> None:
        """
        Handle a message of invalid performative.

        :param contract_api_message: the ledger api message
        :param contract_api_dialogue: the ledger api dialogue
        """
        self.context.logger.warning(
            "[{}]: cannot handle contract_api message of performative={} in dialogue={}.".format(
                self.context.agent_name,
                contract_api_msg.performative,
                contract_api_dialogue,
            )
        )


class SigningHandler(Handler):
    """Implement the transaction handler."""

    SUPPORTED_PROTOCOL = SigningMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        signing_msg = cast(SigningMessage, message)

        # recover dialogue
        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        signing_dialogue = cast(
            Optional[SigningDialogue], signing_dialogues.update(signing_msg)
        )
        if signing_dialogue is None:
            self._handle_unidentified_dialogue(signing_msg)
            return

        # handle message
        if signing_msg.performative is SigningMessage.Performative.SIGNED_MESSAGE:
            self._handle_signed_message(signing_msg, signing_dialogue)
        elif signing_msg.performative is SigningMessage.Performative.ERROR:
            self._handle_error(signing_msg, signing_dialogue)
        else:
            self._handle_invalid(signing_msg, signing_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, signing_msg: SigningMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the message
        """
        self.context.logger.info(
            "[{}]: received invalid signing message={}, unidentified dialogue.".format(
                self.context.agent_name, signing_msg
            )
        )

    def _handle_signed_message(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle a signed message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        :return: None
        """
        fipa_dialogue = (
            signing_dialogue.associated_contract_api_dialogue.associated_fipa_dialogue
        )
        last_fipa_msg = fipa_dialogue.last_incoming_message
        assert last_fipa_msg is not None, "Could not retrieve last fipa message."
        inform_msg = FipaMessage(
            message_id=last_fipa_msg.message_id + 1,
            dialogue_reference=fipa_dialogue.dialogue_label.dialogue_reference,
            target=last_fipa_msg.message_id,
            performative=FipaMessage.Performative.ACCEPT_W_INFORM,
            info={"tx_signature": signing_msg.signed_message.body},
        )
        inform_msg.counterparty = last_fipa_msg.counterparty
        self.context.logger.info(
            "[{}]: sending ACCEPT_W_INFORM to agent={}: tx_signature={}".format(
                self.context.agent_name,
                last_fipa_msg.counterparty[-5:],
                signing_msg.signed_message,
            )
        )
        self.context.outbox.put_message(message=inform_msg)

    def _handle_error(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        :return: None
        """
        self.context.logger.info(
            "[{}]: transaction signing was not successful. Error_code={} in dialogue={}".format(
                self.context.agent_name, signing_msg.error_code, signing_dialogue
            )
        )

    def _handle_invalid(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        :return: None
        """
        self.context.logger.warning(
            "[{}]: cannot handle signing message of performative={} in dialogue={}.".format(
                self.context.agent_name, signing_msg.performative, signing_dialogue
            )
        )


class LedgerApiHandler(Handler):
    """Implement the ledger api handler."""

    SUPPORTED_PROTOCOL = LedgerApiMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        ledger_api_msg = cast(LedgerApiMessage, message)

        # recover dialogue
        ledger_api_dialogues = cast(
            LedgerApiDialogues, self.context.ledger_api_dialogues
        )
        ledger_api_dialogue = cast(
            Optional[LedgerApiDialogue], ledger_api_dialogues.update(ledger_api_msg)
        )
        if ledger_api_dialogue is None:
            self._handle_unidentified_dialogue(ledger_api_msg)
            return

        # handle message
        if ledger_api_msg.performative is LedgerApiMessage.Performative.BALANCE:
            self._handle_balance(ledger_api_msg, ledger_api_dialogue)
        elif ledger_api_msg.performative == LedgerApiMessage.Performative.ERROR:
            self._handle_error(ledger_api_msg, ledger_api_dialogue)
        else:
            self._handle_invalid(ledger_api_msg, ledger_api_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, ledger_api_msg: LedgerApiMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the message
        """
        self.context.logger.info(
            "[{}]: received invalid ledger_api message={}, unidentified dialogue.".format(
                self.context.agent_name, ledger_api_msg
            )
        )

    def _handle_balance(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of balance performative.

        :param ledger_api_message: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(
            "[{}]: starting balance on {} ledger={}.".format(
                self.context.agent_name,
                ledger_api_msg.ledger_id,
                ledger_api_msg.balance,
            )
        )

    def _handle_error(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of error performative.

        :param ledger_api_message: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(
            "[{}]: received ledger_api error message={} in dialogue={}.".format(
                self.context.agent_name, ledger_api_msg, ledger_api_dialogue
            )
        )

    def _handle_invalid(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of invalid performative.

        :param ledger_api_message: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.warning(
            "[{}]: cannot handle ledger_api message of performative={} in dialogue={}.".format(
                self.context.agent_name,
                ledger_api_msg.performative,
                ledger_api_dialogue,
            )
        )
