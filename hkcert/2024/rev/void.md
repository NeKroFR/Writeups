# Void

The challenge provide us a link to a website asking us for a flag:

![alt-text](https://i.imgur.com/mQTkEe1_d.webp?maxwidth=760&fidelity=grand)

Looking at the source code we can see a weird function with some invisible chars:

```html
<!DOCTYPE html>
<html>

<head>
  <meta charset="UTF-8">
  <title>Codeless</title>
  <link rel="stylesheet" href="style.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@300..700&family=Playfair+Display:ital,wght@0,400..900;1,400..900&display=swap" rel="stylesheet">
</head>

<body>
    <div class="container">
        <input type="text" id="flag" placeholder="What is the flag?" onkeydown="handleKeyPress(event)">
    </div>
</body>

<script>
with (ㅤ`` ) {
ㅤㅤㅤㅤㅤㅤㅤ
ㅤㅤㅤㅤ
ㅤㅤㅤㅤㅤㅤㅤ

ㅤ
}
// https://x.com/aemkei/status/1843756978147078286
function \u3164(){return f="",p=[]  
,new Proxy({},{has:(t,n)=>(p.push(
n.length-1),2==p.length&&(p[0]||p[
1]||eval(f),f+=String.fromCharCode
(p[0]<<4|p[1]),p=[]),!0)})}//aem1k
</script>
</html>
```

We can retrieve the function content just using `console.log()`:

```js
> console.log(f)

const flag = document.getElementById('flag');
flag.focus();

handleKeyPress = event => event.key === 'Enter' && check();

function check() {
    if (flag.value === 'hkcert24{....}') {
        flag.disabled = true;
        flag.classList.add('correct');
    } else {
        flag.classList.add('wrong');
        setTimeout(() => flag.classList.remove('wrong'), 500);
    }
}
```