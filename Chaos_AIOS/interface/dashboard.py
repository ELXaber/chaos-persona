from flask import Flask, request, jsonify
import interface

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def dashboard():
    if request.method == "POST":
        data = request.json
        return jsonify({"response": interface.caios(
            data["message"],
            data.get("agent", "day"),
            data.get("show_reasoning", False),
            data.get("show_cot", False),
            data.get("personality", None)
        )})
    # return HTML with sliders + chat UI
    return """
    <h1>Chaos AI-OS Dashboard</h1>
    <input id="msg" placeholder="Talk to any agent">
    <button onclick="send()">Send</button>
    <div>Sliders for professional/snarky/etc here...</div>
    <pre id="out"></pre>
    <script>
      function send() {
        fetch("/", {method:"POST", body:JSON.stringify({message: msg.value, agent:"day", personality:{snarky:8}})})
          .then(r => r.json()).then(d => out.textContent += d.response + "\n\n");
      }
    </script>
    """

if __name__ == "__main__":
    app.run(port=5000)
