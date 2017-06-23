package main

import (
	"encoding/json"
	"fmt"
	"github.com/satori/go.uuid"
	// "html"
	"html/template"
	"log"
	"net/http"
)

type MessagesMap map[string][]Message

type MessageBuffer struct {
	Waiters []*Client
}

func (m *MessageBuffer) NewWaiter(c *Client) {
	m.Waiters = append(m.Waiters, c)
}

func (m *MessageBuffer) NewMessage(c *Message) {
	d := make(MessagesMap)
	message_list := []Message{*c} //提取指针指向的 message
	d["messages"] = message_list
	for _, w := range m.Waiters {
		if w != nil {
			jsonMsg, _ := json.Marshal(d)
			w.c <- jsonMsg //向等待的连接发送消息
		}
	}
	m.Waiters = make([]*Client, 10) //清空 waiterrs
}

type Client struct {
	id string
	c  chan []byte
}

type Message struct {
	Id   string `json:"id,omitempty"`
	Body string `json:"body,omitempty"`
	Html string `json:"html,omitempty"`
}

func MainHandler(w http.ResponseWriter, r *http.Request) {
	tmpl := template.Must(template.ParseFiles("templates/index.html"))
	tmpl.Execute(w, nil)
}

func MessageNewHandler(w http.ResponseWriter, r *http.Request) {
	//解析参数
	message := Message{
		Id:   uuid.NewV4().String(),
		Body: r.FormValue("body"),
	}
	htmlMsg := fmt.Sprintf(`<div class="message" id="m%s">%s</div>`, message.Id, message.Body)
	message.Html = htmlMsg
	messageBuffer.NewMessage(&message)
}

func MessageUpdatesHandler(w http.ResponseWriter, r *http.Request) {
	client := Client{id: uuid.NewV4().String(), c: make(chan []byte)}
	messageBuffer.NewWaiter(&client)
	msg := <-client.c //挂起请求等待消息来临
	w.Header().Set("Content-Type", "application/json")
	w.Write(msg)
}

var messageBuffer = MessageBuffer{
	Waiters: make([]*Client, 10),
}

func main() {
	http.HandleFunc("/", MainHandler)
	http.HandleFunc("/a/message/new", MessageNewHandler)
	http.HandleFunc("/a/message/updates", MessageUpdatesHandler)
	fs := http.FileServer(http.Dir("static/"))
	http.Handle("/static/", http.StripPrefix("/static/", fs))
	log.Println("open browser http://localhost:8889")
	err := http.ListenAndServe(":8889", nil) //设置监听的端口
	if err != nil {
		log.Fatal("ListenAndServe: ", err)
	} else {
		log.Println("server star")
	}
}
