# MARTSIA-EVM-OnChain

**Multi-Authority Approach to Transaction Systems for Interoperating Applications**  
**** 

This version of MARTSIA-Demo carries out the request and transmission of key segments between the Reader and Authorities through the blockchain using RSA encryption.
We implemented the smart contract for this MARTSIA version in Solidity, making it EVM-compatible.

## Wiki
For a detailed documentation and step-by-step tutorial to run this version locally, check out the [Wiki](https://github.com/apwbs/MARTSIA-Demo-KoB/wiki).

## This repository
In this repository you find several folders necessary to run the system. 
1. The *blockchain* folder contains all the necessary data to connect to the blockchain. For example, the smart contract code in the *contracts* folder, the JavaScript code to deploy on-chain the smart contract in the *migrations* folder, and finally the *truffle-config.js* file to connect to the blockchain via Truffle.
2. In the *databases* folder you find the SQL files to build the auxiliary relational tables we use in this prototypical implementation of our system to store temporary data (yellow pages, seeds, RSA private keys, etc.).
3. The *input_files* folder is the folder where to put the files to encrypt. You can use whatever folder you desire.
4. The *json_files* folder contains the files that specify the roles of the actors involved in the process and the access policies. You can use whatever folder you desire.
5. The *output_files* folder is the folder where decrypted files are saved. You can use whatever folder you desire.
6. In the *sh_files* folder you find all the sh files to use MARTSIA. These files simplify usage and hide complex steps, making MARTSIA more user-friendly for the end user.
7. The *src* folder contains the Python scripts that are run through the sh files. 

## MARTSIA main GitHub page
For more details about MARTSIA, refer to the [main MARTSIA GitHub page](https://github.com/apwbs/MARTSIA).
