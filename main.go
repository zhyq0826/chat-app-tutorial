package main

import (
	// "fmt"
	"html/template"
	"log"
	"net/http"
)

func MainHandler(w http.ResponseWriter, r *http.Request) {
	t := template.New("index")
	t.ParseFiles("templates/index.html")
	t.Execute(w, nil)
}

func MessageNewHandler(w http.ResponseWriter, r *http.Request) {

}

func MessageUpdatesHandler(w http.ResponseWriter, r *http.Request) {

}

func main() {
	http.HandleFunc("/", MainHandler)
	http.HandleFunc("/a/message/new", MessageNewHandler)
	http.HandleFunc("/a/message/updates", MessageUpdatesHandler)
	err := http.ListenAndServe(":8889", nil) //设置监听的端口
	if err != nil {
		log.Fatal("ListenAndServe: ", err)
	}
}
