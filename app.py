from flask import Flask, request, render_template, jsonify, send_file
from zep_cloud.client import Zep
import os
import json
from dotenv import load_dotenv
from pyvis.network import Network

# === 加载配置 ===
load_dotenv()
API_KEY = os.environ.get("ZEP_API_KEY")
client = Zep(api_key=API_KEY)

# === 固定用户 ID ===
FIXED_USER_ID = "001"
# print(client.graph.node.get_by_user_id(FIXED_USER_ID))

app = Flask(__name__)

# === 首页页面 ===
@app.route("/")
def index():
    return render_template("index.html")


# === 创建项目接口 ===
@app.route("/create_project", methods=["POST"])
def create_project():
    try:
        # 从前端表单或 JSON 取出项目名（作为 user_id）
        project_name = request.form.get("project_name") or request.json.get("project_name")
        if not project_name:
            return jsonify({"status": "error", "message": "Missing project name"}), 400

        user_id = project_name  # 用项目名作为 user_id

        # 可以自定义项目的 email/first_name/last_name，这里简单生成
        new_user = client.user.add(
            user_id=user_id,
            email=f"{user_id}@auto.project",
            first_name=project_name,
            last_name="Project"
        )

        return jsonify({"status": "success", "message": f"Project '{project_name}' created.", "user_id": user_id})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# === 提交笔记接口 ===
@app.route("/submit", methods=["POST"])
def submit_note():
    try:
        project_name = request.form.get("project_name")
        article_title = request.form.get("article_title")
        origin = request.form.get("origin")
        comment = request.form.get("comment")

        if not all([project_name, article_title, origin]):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        note = {
            "content": {
                "project_name": project_name,
                "article_title": article_title,
                "origin": origin,
                "comment": comment or ""
            }
        }

        json_data = json.dumps(note["content"], ensure_ascii=False)

        res = client.graph.add(
            user_id=project_name,  # 用 project_name 作为 user_id
            type="json",
            data=json_data
        )
        return jsonify({"status": "success", "message": "Note added successfully!"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/graph")
def generate_graph():
    user_id = request.args.get("user_id")
    if not user_id:
        return "Missing user_id (project_name)", 400

    try:
        nodes = client.graph.node.get_by_user_id(user_id)
        edges = client.graph.edge.get_by_user_id(user_id)

        net = Network(height='1000px', width='100%', directed=True)

        for node in nodes:
            label = node.name or "no name"
            net.add_node(node.uuid_, label=label, title=node.summary or "")

        for edge in edges:
            src = edge.source_node_uuid
            tgt = edge.target_node_uuid
            label = edge.name or "relation"
            net.add_edge(src, tgt, label=label, title=edge.fact or "")

        net.set_options("""var options = {
          "physics": {
            "enabled": true,
            "stabilization": {
              "enabled": true,
              "iterations": 200
            },
            "forceAtlas2Based": {
              "gravitationalConstant": -50,
              "centralGravity": 0.01,
              "springLength": 120,
              "springConstant": 0.08,
              "damping": 0.4,
              "avoidOverlap": 1
            },
            "minVelocity": 0.75,
            "solver": "forceAtlas2Based"
          }
        }""")

        graph_path = f"static/graph_output_{user_id}.html"
        net.write_html(graph_path)
        return send_file(graph_path)

    except Exception as e:
        return f"图谱生成失败：{str(e)}", 500


# # 动态图谱数据接口
# @app.route("/graph_data")
# def graph_data():
#     try:
#         nodes = client.graph.node.get_by_user_id(FIXED_USER_ID)
#         edges = client.graph.edge.get_by_user_id(FIXED_USER_ID)

#         def to_vis():
#             vis_nodes = []
#             for node in nodes:
#                 vis_nodes.append({
#                     "id": node.uuid_,
#                     "label": node.name or "Unnamed",
#                     "title": node.summary or ""
#                 })

#             vis_edges = []
#             for edge in edges:
#                 vis_edges.append({
#                     "from": edge.source_node_uuid,
#                     "to": edge.target_node_uuid,
#                     "label": edge.name or "",
#                     "title": edge.fact or "",
#                     "arrows": "to"
#                 })

#             return {"nodes": vis_nodes, "edges": vis_edges}

#         return jsonify(to_vis())
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@app.route("/search", methods=["POST"])
def search_nodes_or_episodes():
    try:
        query = request.form.get("query")
        project_name = request.form.get("project_name")
        scope = request.form.get("scope", "nodes")  # 默认搜 nodes
        if not query:
            return jsonify({"status": "error", "message": "Missing search query"}), 400

        search_results = client.graph.search(
            user_id=project_name,
            query=query,
            scope=scope,
            limit=3,
        )

        result_list = []
        if scope == "nodes":
            for idx, node in enumerate(search_results.nodes, start=1):
                result_list.append({
                    "type": "node",
                    "index": idx,
                    "name": node.name,
                    "summary": node.summary,
                    "created_at": node.created_at,
                })
        elif scope == "episodes":
            for idx, ep in enumerate(search_results.episodes, start=1):
                content = json.loads(ep.content)
                result_list.append({
                    "type": "episode",
                    "index": idx,
                    "project_name": content.get("project_name", ""),
                    "article_title": content.get("article_title", ""),
                    "origin": content.get("origin", ""),
                    "comment": content.get("comment", ""),
                    "created_at": ep.created_at,
                })

        return jsonify({"status": "success", "results": result_list})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



if __name__ == "__main__":
    app.run(debug=True)
