# Climb Tracker

Ventana pequeña para la segunda pantalla con el rango, el MMR y la racha de los jugadores que quieras seguir en Rocket League. No toca el juego: consulta los datos de rocketleague.tracker.network y, si la activas, lee la Stats API oficial del juego para saber cuándo acaba cada partida y quién juega en ella.

## Instalarlo

No hay que instalar nada:

1. Descarga **`Climb-Tracker-vX.Y.Z-windows.zip`** de la [última versión](https://github.com/mafiaki/climb-tracker/releases/latest).
2. Descomprímelo donde quieras (Escritorio, Documentos, un USB…).
3. Abre **`Climb Tracker.exe`**.

La primera vez Windows puede avisar con «Windows protegió tu PC» porque el programa no está firmado: pulsa **Más información → Ejecutar de todas formas**. Funciona en Windows 10 y 11 (usa WebView2, que ya viene con Windows).

La carpeta es portable: puedes moverla o copiarla adonde quieras. Tu lista de jugadores y tus ajustes se guardan en su carpeta `data/`, que es solo tuya.

## Actualizaciones

Al abrirse, la app mira si hay una versión nueva en GitHub y, si la hay, avisa abajo con un botón **Actualizar**: baja la versión nueva, la pone encima sin tocar `data/` (tus jugadores y ajustes siguen igual) y se vuelve a abrir sola. También puedes buscarla a mano en **Ajustes → Versión → Buscar actualizaciones**.

## Desde el código (opcional)

Si prefieres usarla con tu Python (3.11 o más nuevo): descarga el código, abre `Iniciar Climb Tracker.bat` la primera vez (instala `pywebview` y `curl_cffi`) y luego `Climb Tracker.pyw`. Para crear la versión portable: `pip install pyinstaller` y `python tools/build.py`. El icono se genera con `python tools/make_icon.py`.

## Qué muestra

- Rango, división y MMR de la lista de juego elegida (pestañas de arriba: 1v1, 2v2, 3v3, Torneo, Hoops…).
- ▲ MMR que falta para subir de división, ▼ MMR que puedes perder sin bajar, y lo que falta para el siguiente rango.
- Partidas jugadas en la temporada, la racha actual y el MMR ganado o perdido **hoy** y en la **sesión**. La sesión empieza cuando pulsas la bandera de arriba (p. ej. al pasar de jugar solo a jugar con un amigo; sale «Deshacer» por si fue sin querer). En Ajustes eliges ver Hoy, Sesión o Ambos.
- Al hacer clic en un jugador: gráfica de MMR con las líneas de cada división y rango (pasa el ratón por encima para ver el MMR de cada partida), últimas partidas (+/− MMR) y el MMR en las otras listas.
- Para reordenar tu lista, arrastra una tarjeta cogiéndola por la barra de color de la izquierda.

Botones de arriba: actualizar, fijar encima de otras ventanas, ajustes (vista compacta, frecuencia) y **+** para añadir jugadores (Steam, Epic, PlayStation, Xbox o Switch; vale el nombre, el ID o el enlace del perfil).

## Partida en curso (opcional, con la Stats API del juego)

Con la Stats API activada (ver abajo), la app sabe cuándo empieza y acaba cada partida:

- **MMR al momento:** al acabar una partida, en la tarjeta de los de tu lista que jugaban sale **Victoria** o **Derrota · actualizando MMR…** y la app pide su perfil a Tracker en cuanto tiene el dato nuevo (a los ~15 s, o cuando caduca la caché de Tracker, ~6 min como mucho). Si el MMR aún no ha cambiado, vuelve a mirar un par de veces más y luego sigue con su ritmo normal. Las partidas privadas, de exhibición o de entreno no cuentan.
- **Jugadores de la partida** (apagado por defecto; se enciende en Ajustes con «Mostrar debajo a los jugadores de la partida»): debajo de tu lista, para que tus tarjetas no se muevan, sale **En partida** con los jugadores separados en azul y naranja. Ves su rango, su MMR y lo que les falta para subir, y el MMR medio de cada equipo. El rango es el de la pestaña que tengas elegida arriba (útil si juegas Casual y quieres ver su 2v2); en Ajustes puedes cambiarlo a «Lista de la partida». Con el **+** pasas a alguien a tu lista fija (✓ = ya está). Al acabar se pliega en una sola línea, **Última partida**, que se abre con un clic. La ✕ la oculta hasta la próxima partida.

Usa la [Stats API oficial de Rocket League](https://www.rocketleague.com/developer/stats-api): una función del propio juego, pensada para overlays, que publica los datos de la partida en un puerto local (127.0.0.1). La app solo escucha ese puerto: no lee la memoria del juego ni se engancha a su proceso.

**Cómo activarla (una vez):**

1. Abre **Ajustes → Partida en curso**. La app busca sola el juego (Steam o Epic); si no lo encuentra, pulsa **Elegir carpeta…** y elige la carpeta del juego (la que tiene `TAGame` y `Binaries`; en Steam suele ser `steamapps\common\rocketleague`).
2. Pulsa **Activar Stats API**. Cambia `PacketSendRate=0` por `PacketSendRate=5` en `TAGame\Config\DefaultStatsAPI.ini` (o en `TAStatsAPI.ini` si existe) y deja una copia del original al lado (`.bak`). No toca nada más.
3. Reinicia Rocket League. En Ajustes verás «Conectado con Rocket League» con el juego abierto.

**A mano**, si lo prefieres (o si Windows no deja escribir en la carpeta): con el juego cerrado, abre ese archivo con el Bloc de notas (botón **Abrir carpeta**) y en la sección `[TAGame.MatchStatsExporter_TA]` pon `PacketSendRate=5` (de 1 a 120; 0 la apaga). Deja `Port=49123`, que es el puerto que escucha la app. **Desactivar** vuelve a ponerlo a 0.

Sin el juego abierto (o sin la API activada) la app funciona igual, con su refresco normal: reintenta conectar en silencio cada pocos segundos.

## Límites

- No hay API oficial de rangos. Esto usa la API interna de Tracker Network, que puede cambiar o bloquearse sin aviso.
- Tracker refresca cada perfil como mucho cada ~6 minutos, así que una partida tarda unos minutos en aparecer.
- Tracker a veces junta varias partidas en una sola entrada o marca mal victoria/derrota. La app se fía del cambio de MMR.
- En partida: los de Steam y Epic se buscan por su ID; los de PlayStation, Xbox y Switch por el nombre que se ve en el juego, así que a veces Tracker no los encuentra. Los bots y los invitados de pantalla dividida no tienen rango. Cada jugador tarda ~1,5 s en cargar (las consultas van en fila para no abusar de Tracker).
- Las actualizaciones del juego pueden devolver `DefaultStatsAPI.ini` a 0. Si lo activaste desde la app, te avisará debajo de tu lista con un botón para activarlo otra vez.
