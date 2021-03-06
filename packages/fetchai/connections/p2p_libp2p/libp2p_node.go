/* -*- coding: utf-8 -*-
* ------------------------------------------------------------------------------
*
*   Copyright 2018-2019 Fetch.AI Limited
*
*   Licensed under the Apache License, Version 2.0 (the "License");
*   you may not use this file except in compliance with the License.
*   You may obtain a copy of the License at
*
*       http://www.apache.org/licenses/LICENSE-2.0
*
*   Unless required by applicable law or agreed to in writing, software
*   distributed under the License is distributed on an "AS IS" BASIS,
*   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
*   See the License for the specific language governing permissions and
*   limitations under the License.
*
* ------------------------------------------------------------------------------
 */

package main

import (
	"fmt"
	"log"
	"os"
	"os/signal"

	"github.com/rs/zerolog"

	aea "libp2p_node/aea"
	"libp2p_node/dht/dhtclient"
	"libp2p_node/dht/dhtnode"
	"libp2p_node/dht/dhtpeer"
	"libp2p_node/utils"
)

var logger zerolog.Logger = utils.NewDefaultLogger()

// panics if err is not nil
func check(err error) {
	if err != nil {
		panic(err)
	}
}

func ignore(err error) {
	if err != nil {
		log.Println("IGNORED", err)
	}
}

func main() {

	var err error

	// Initialize connection to aea
	agent := aea.AeaApi{}
	check(agent.Init())
	log.Println("successfully initialized API to AEA!")

	// Get node configuration

	// aea agent address
	aeaAddr := agent.AeaAddress()

	// node address (ip and port)
	nodeHost, nodePort := agent.Address()

	// node public address, if set
	nodeHostPublic, nodePortPublic := agent.PublicAddress()

	// node delegate service address, if set
	_, nodePortDelegate := agent.DelegateAddress()

	// node private key
	key := agent.PrivateKey()

	// entry peers
	entryPeers := agent.EntryPeers()

	// libp2p node
	var node dhtnode.DHTNode

	// Run as a peer or just as a client
	if nodePortPublic == 0 {
		// if no external address is provided, run as a client
		opts := []dhtclient.Option{
			dhtclient.IdentityFromFetchAIKey(key),
			dhtclient.RegisterAgentAddress(aeaAddr, agent.Connected),
			dhtclient.BootstrapFrom(entryPeers),
		}
		node, err = dhtclient.New(opts...)
	} else {
		opts := []dhtpeer.Option{
			dhtpeer.LocalURI(nodeHost, nodePort),
			dhtpeer.PublicURI(nodeHostPublic, nodePortPublic),
			dhtpeer.IdentityFromFetchAIKey(key),
			dhtpeer.RegisterAgentAddress(aeaAddr, agent.Connected),
			dhtpeer.EnableRelayService(),
			dhtpeer.EnableDelegateService(nodePortDelegate),
			dhtpeer.BootstrapFrom(entryPeers),
		}
		node, err = dhtpeer.New(opts...)
	}

	if err != nil {
		check(err)
	}
	defer node.Close()

	// Connect to the agent
	fmt.Println("MULTIADDRS_LIST_START") // keyword
	fmt.Println(node.MultiAddr())
	fmt.Println("MULTIADDRS_LIST_END") // keyword

	check(agent.Connect())
	logger.Info().Msg("successfully connected to AEA!")

	// Receive envelopes from agent and forward to peer
	go func() {
		for envel := range agent.Queue() {
			envelope := envel
			logger.Info().Msgf("received envelope from agent: %s", envelope)
			go func() {
				err := node.RouteEnvelope(envelope)
				ignore(err)
			}()
		}
	}()

	// Deliver envelopes received fro DHT to agent
	node.ProcessEnvelope(func(envel *aea.Envelope) error {
		return agent.Put(envel)
	})

	// Wait until Ctrl+C or a termination call is done.
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt)
	<-c

	logger.Info().Msg("node stopped")
}
