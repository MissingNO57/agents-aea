<details><summary>What is the Open Economic Framework (OEF)?</summary>
The 'Open Economic Framework' (OEF) is a node that enables us to search, discover and communicate with possible clients or services. 
<br><br>
You can read more about the ledgers and the OEF <a href="/oef-ledger/"> here </a>
</details>

<details><summary>What is the AEA?</summary>
AEA is short for Autonomous Economic Agents. AEAs act independently of constant user input and autonomously execute actions to achieve their objective.
Their goal is to create economic value for you, their owner. 
<br><br>
You can read more about the AEAs <a href="/app-areas/"> here </a>
</details>

<details><summary>How do agents talk to each other who don't know each other?</summary>
For the Autonomous Economic Agents (AEAs) to be able to talk to each other. Firstly, they need to find each other, 
and then, implement the same protocols in order to be able to deserialize the envelops they receive.
<br><br>
You can read more about the Search and Discovery <a href="/oef-ledger/">here</a> and more about envelops and protocols <a href="/core-components/">here</a>

</details>

<details><summary>How does an AEA use blockchain?</summary>
The AEA framework enables the agents to interact with public blockchains to complete transactions. Currently, the framework supports
two different networks natively: the `Fetch.ai` network and the `Ethereum` network. 
<br><br>
You can read more about the intergration of ledger <a href="/integration/">here</a>

</details>

<details><summary>How does one install third party libraries?</summary>
The framework enables us to use third-party libraries hosted on PyPI we can directly reference the external dependencies.
The `aea install` command will install each dependency that the specific AEA needs and is listed in the skill's YAML file.

<details><summary>How does one connect a DB?</summary>
If you want to connect a database you have two options. Either create a wrapper that communicates with the database and imported in a Model,
you can find this implementation in the weather_station package, or use ORM (Object-relational-mapping), you have to implement the logic inside 
a class that inherits from the Model abstract class.
<br><br>
For a detailed example of how to use ORM follow the <a href='/orm-integration-to-generic/'>ORM use case</a>  
</details>

<details><summary>How does one connect a lifestream of data?</summary>
You can create a wrapper class that communicates with the source and import this class in your skill,
or you can use a third-party library by listing the dependency in the skill's `.yaml` file. Then you can import this library in a strategy class that inherits
from the Model abstract class.
<br><br>
You can find example of this implementation in the <a href='/thermometer-skills-step-by-step/#step4-create-the-strategy_1'> thermometer step by step guide </a>
</details>

<details><summary>How does one connect a frontend?</summary>
There are two options that one could connect a frontend. The first option would be to create an HTTP connection and then create an app that will communicate with this
connections.
The other option is to create a Frontend client that will communicate with the agent via the OEF.
<br><br>
You can find a more detailed approach <a href="/connect-a-frontend/">here</a>
</details>

<details><summary>Is the AEA framework ideal for agent based modelling?</summary>
The goal of agent-based modeling is to search for explanatory insight into the collective behavior of agents obeying simple rules, typically in natural systems rather than in designing agents or solving specific practical or engineering problems. 
Although it would be potentially possible, it would be inefficient to use the AEA framework for that kind of problem.
<br><br>
You can find more details <a href="/app-areas/">here</a>
</details>
