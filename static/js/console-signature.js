/* LinkedTrust — branded console signature
 * A small easter egg for the curious developer.
 * Deep Tech. Human Trust.  →  connect@linkedtrust.us
 */
(function () {
  "use strict";

  // Guard: only run once per page, and skip non-browser / no-console contexts.
  if (typeof window === "undefined" || !window.console || !console.log) {
    return;
  }
  if (window.__ltConsoleSignature) {
    return;
  }
  window.__ltConsoleSignature = true;

  var CYAN = "#00B2E5";
  var PURPLE = "#667eea";

  // The LinkedTrust mark (ASCII art). Stored as a template string.
  var art = [
    "               @@@%@@@@@@@@@@%@@@",
    "           @@@@@@@@@@@@@@@@@@@@@@@@@@",
    "         %@@@@==%@@@@@*--+@@@@@*:+@@@%%",
    "      @%@@@@@@:::=@@@+::::+@@%:::-@@@@@@%",
    "     @@@@@@@@@-:::#@*::::::*@::::+@@@@@@@@@",
    "   @@@@@@@@@@@@+-:%@-::::::-@-::*@@@@@@@@@@@#",
    "  @@@@@@@@=---+#@@@#::::::::%@@@#=:::-@@@@@@@@",
    " @@@@@@@@@=------=@@-::::::-@@-::::::-@@@@@@@@",
    " @@#--=*@@*--------@@-::::-@%::::::::+@%****@@#",
    "@@@@-----#@---------@@=::-@@:::::::::@*++++#@@@*",
    "@@@@@#+---%@--------%@@==@@#::::::::@*++**@@@@@#",
    "@@@@@@@@@@@@@#=-----*@@==@@+:::::-*@@@%%%%%@@@@@",
    "@@@@@=------=+#@@#*-=@@::@@::=*@@#*++++++++@@@@@",
    "@@@@@@----------#@@@::@::@::@@@#++++++++++@@@@@@",
    "#@@@@@@----------#@@@::::::@@@#++++++++++%@@@@@#",
    "%@@@@@@@*---------#@@+::::#@@#+++++++++*@@@@@@@%",
    "@@@@@@@@@@#*=---==-+@@::::@@+-+++++**#@@@@@@@@@@",
    " #@@@@@@@@@@@@##%@@::@:::-@::@%##%@@@@@@@@@@@@#",
    "  #@@@@@@@@%=-----*@::=::+::@*+++++*@@@@@@@@@%",
    "   *@@@@@@@@@%###@@@@::::::@@@@###%@@@@@@@@@*",
    "    +*@@@@@@@@@@@@@@@+::::*@@@@@@@@@@@@@@@*=",
    "      :*@@@@@@@@@@@@@@::::@@@@@@@@@@@@@@*-",
    "        **@@@@@@@@@@@@::::@@@@@@@@@@@@**",
    "           =+#@@@@@@%::::::@@@@@@@#+=",
    "               .::::::::::::::::."
  ].join("\n");

  // Each entry is a [message, css] pair logged in sequence.
  var lines = [
    [
      "%c" + art,
      "color:" + CYAN + ";font-family:monospace;line-height:1.05;font-size:10px;"
    ],
    [
      "%cLinkedTrust — Deep Tech. Human Trust.",
      "color:" + CYAN + ";font-weight:bold;font-size:18px;font-family:monospace;" +
        "text-shadow:0 1px 0 rgba(102,126,234,.35);"
    ],
    [
      "%cPoking around the console? We like you already.",
      "color:" + PURPLE + ";font-size:13px;font-family:monospace;"
    ],
    [
      "%cOpen source-minded, cooperatively built — and every testimonial is a verifiable LinkedClaim.",
      "color:#9aa3b2;font-size:13px;font-family:monospace;"
    ],
    [
      "%cLike building real things with real trust?  →  connect@linkedtrust.us",
      "color:" + CYAN + ";font-weight:bold;font-size:13px;font-family:monospace;"
    ]
  ];

  // Reveal lines sequentially for a subtle cascade effect.
  var STEP = 150; // ms between lines; full sequence stays under ~1.5s
  lines.forEach(function (line, index) {
    window.setTimeout(function () {
      console.log(line[0], line[1]);
    }, index * STEP);
  });
})();
