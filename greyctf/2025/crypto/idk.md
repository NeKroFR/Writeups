# idk

This is a ZKP challenge where we need to recover a flag which has been encrypted using RSA. To do it, we are given two network dumps, the prover and verifier scripts, and the RSA parameters.

The prover generates `sigmas` and `mus`:

```py
sigmas = []
invN_mod_phi = inverse(N, phi)
for i in range(1, m1 + 1):
    rho_i = gen_rho_ZN(N, i)
    sigma_i = pow(rho_i, invN_mod_phi, N)
    sigmas.append(sigma_i)

...

mus = []
for j in range(1, m2 + 1):
    theta_j = gen_theta_J(N, m1 + j, F_bytes)

    if pow(theta_j, (p - 1) // 2, p) == 1 and pow(theta_j, (q - 1) // 2, q) == 1:
        r_p = tonelli(theta_j % p, p)
        r_q = tonelli(theta_j % q, q)
        if random.random() < flip_prob:
            r_p = -r_p % p
        mu_j = crt_combine(r_p, p, r_q, q)
        mus.append(mu_j)
    else:
        mus.append(0)
```

The vulnerability lies in the random sign flip in the `mus` generation. When the same `theta_j` in two dumps results in different sign choices (for example: `mu1 = CRT(r_p, r_q)` and `mu2 = CRT(-r_p, r_q)`), their difference `mu1 - mu2 = 2*r_p*p` is divisible by `p`. So we can retrieve `p` computing `GCD((mu1 - mu2) % N, N)`

To solve the challenge, we extract the relevant values from the dump to factorize `N` and get the flag.

## solve.py:
```py
from Crypto.Util.number import GCD, inverse, long_to_bytes
from math import ceil, log2

def read_dump(filename):
    with open(filename, 'r') as f:
        lines = f.read().strip().split('\n')
    F_bytes = bytes.fromhex(lines[0])
    sigmas = [int(x, 16) for x in lines[1:m1+1]]
    mus = [int(x, 16) for x in lines[m1+1:m1+m2+1]]
    return F_bytes, sigmas, mus

N = 15259097618051614944787283201589661884102249046616617256551480013493757323043057001133186203348289474506700039004930848402024292749905563056243342761253435345816868449755336453407731146923196889610809491263200406510991293039335293922238906575279513387821338778400627499247445875657691237123480841964214842823837627909211018434713132509495011638024236950770898539782783100892213299968842119162995568246332594379413334064200048625302908007017119275389226217690052712216992320294529086400612432370014378344799040883185774674160252898485975444900325929903357977580734114234840431642981854150872126659027766615908376730393
e = 65537
c = 6820410793279074698184582789817653270130724082616000242491680434155953264066785246638433152548701097104342512841159863108848825283569511618965315125022079145973783083887057935295021036668795627456282794393398690975486485865242636068814436388602152569008950258223165626016102975011626088643114257324163026095853419397075140539144105058615243349994512495476754237666344974066561982636000283731809741806084909326748565899503330745696805094211629412690046965596957064965140083265525186046896681441692279075201572766504836062294500730288025016825377342799012299214883484810385513662108351683772695197185326845529252411353

kappa = 128
alpha = 65537
m1 = ceil(kappa / log2(alpha))
m2 = ceil(kappa * 32 * 0.69314718056)

F_bytes1, sigmas1, mus1 = read_dump('dump1.txt')
F_bytes2, sigmas2, mus2 = read_dump('dump2.txt')

for j in range(m2):
    mu1, mu2 = mus1[j], mus2[j]
    if mu1 != 0 and mu2 != 0:
        diff = (mu1 - mu2) % N
        if diff == 0:
            continue
        p = GCD(diff, N)
        if 1 < p < N:
            break
else:
    raise ValueError("No factor found")

q = N // p
phi = (p - 1) * (q - 1)
d = inverse(e, phi)

m = pow(c, d, N)
flag = long_to_bytes(m).decode()
print(flag)
```
