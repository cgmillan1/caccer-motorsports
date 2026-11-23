# Caccer Motorsports

Website de Caccer Motorsports (West Jordan, UT) y la app de negocio de Santi.

- `index.html` + `img/`: website con los autos disponibles, visor con fotos reales, precios OTD, mensaje directo por Instagram en español o inglés.
- `santi/`: app de Santi para inventario, ventas, Airbnb, gastos y resumen de sales tax trimestral y anual.

## Cambiar o agregar un auto
Editá la lista `CARS` en `index.html` (precio, millas, specs, features en `en` y `es`) y subí las fotos a `img/` con el nombre `<id>_01.jpg`, `<id>_02.jpg`...
Para un giro 360 completo, poné 24 a 36 fotos alrededor del auto en `photos.ext`, en orden.

## Link directo a un auto
`https://cgmillan1.github.io/caccer-motorsports/#trx` (ids: trx, velar, rav4, crv, f150)

## Intro de la página
Al entrar por primera vez (sin `#auto` en el link) se ve `img/intro_trx.mp4`: la TRX se dibuja con luz y su último cuadro, que es exactamente `img/trx_01.jpg`, vuela hasta el visor mientras aparece el resto de la página.
Se muestra una vez por visita, se puede saltar, y no aparece con "reducir movimiento" ni con ahorro de datos.
Si cambiás la foto `trx_01.jpg`, hay que volver a generar el video para que termine en la foto nueva.
