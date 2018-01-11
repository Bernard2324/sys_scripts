#!/usr/bin/env python

from Crypto.Cipher import DES


# let password =
passw = "myhouse81"

deobfuscator = "".join(chr(i+3) for i in map(ord, [x for x in passw]))

# choose any 8 char. key
key = 'abcdefgh'




def encryption():
	skey = '123yub9**c'

	object = DES.new(skey, DES.MODE_ECB)
	return object.encrypt(deobfuscator)

cipher_text = encryption()

def decrypter(ekey):
	if not isinstance(ekey, str):
		ekey = str(ekey)

	object = DES.new(ekey, DES.MODE_ECB)
	cipher = cipher_text

	return object.decrypt(cipher)


# now to get the password

password = "".join(chr(i-3) for i in map(ord, [j for j in decrypter(key)]))

'''
instructions:

1. In a python interactive shell, run the deobfuscator function against your password.  
	(This can be done using the python interactive shell in linux.)

2. Manually use the encryption function, replacing the static key with that of your choice, to return the encrypted cipher object.
   (This can be done using the python interactive shell in linux.)

3.  Take the cipher and place that inside the decrypter() function.  Place this function in a script.  To decrypt the deobfuscator, you 
	must supply the proper secret key.  This key will be used to build the DES object; used later to decrypt.  the wrong key will result
	in the wrong deobfuscator.  The decrypted deobfuscator will be passed to the password "".join() statement.  Only the one who knows the 
	obfuscation pattern used to obfuscate, can deobfuscate.  I used (i - 3) for simplicity, but you can use any mathmatical implementation you
	desire, so long as it's repeated for obfuscation and deobfuscation.

4. This will allow a script to connect to a service, by supplying the secret key.  If the script is on a compromised server, the attacker will have no
	possibility of knowing the password; at most, he/she will be able to execute the script.  Credentials are not revealed.