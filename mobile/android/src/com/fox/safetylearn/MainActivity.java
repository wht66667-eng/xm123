package com.fox.safetylearn;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.DownloadManager;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.view.View;
import android.view.WindowInsets;
import android.webkit.CookieManager;
import android.webkit.JsResult;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public class MainActivity extends Activity {
 private WebView web;
 private TextView status;
 private String server="";
 private static final String LOCAL="https://fox.local/";
 @Override public void onCreate(Bundle state){
  super.onCreate(state);
  getWindow().setStatusBarColor(Color.rgb(23,60,50));
  getWindow().setNavigationBarColor(Color.rgb(245,244,237));
  LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(Color.rgb(245,244,237));
  root.setOnApplyWindowInsetsListener((v,i)->{if(android.os.Build.VERSION.SDK_INT>=30){android.graphics.Insets in=i.getInsets(WindowInsets.Type.systemBars());v.setPadding(in.left,in.top,in.right,in.bottom);}else{v.setPadding(i.getSystemWindowInsetLeft(),i.getSystemWindowInsetTop(),i.getSystemWindowInsetRight(),i.getSystemWindowInsetBottom());}return i;});
  LinearLayout bar=new LinearLayout(this);bar.setPadding(8,4,8,4);
  button(bar,"离线题库",()->offline());button(bar,"连接服务",()->settings());button(bar,"复制脚本",()->copyScript());
  root.addView(bar);
  status=new TextView(this);status.setTextColor(Color.rgb(23,60,50));status.setPadding(16,4,16,8);status.setTextSize(12);root.addView(status);
  web=new WebView(this);web.setBackgroundColor(Color.rgb(245,244,237));root.addView(web,new LinearLayout.LayoutParams(-1,0,1));
  setContentView(root);
  web.getSettings().setJavaScriptEnabled(true);web.getSettings().setDomStorageEnabled(true);web.getSettings().setAllowFileAccess(false);web.getSettings().setAllowContentAccess(false);web.getSettings().setJavaScriptCanOpenWindowsAutomatically(false);
  CookieManager.getInstance().setAcceptCookie(true);
  web.setWebChromeClient(new WebChromeClient(){
   @Override public boolean onJsConfirm(WebView v,String url,String message,JsResult result){new AlertDialog.Builder(MainActivity.this).setMessage(message).setPositiveButton("确认",(d,w)->result.confirm()).setNegativeButton("取消",(d,w)->result.cancel()).setOnCancelListener(d->result.cancel()).show();return true;}
  });
  web.setWebViewClient(new WebViewClient(){
   @Override public WebResourceResponse shouldInterceptRequest(WebView v,WebResourceRequest r){
    if("fox.local".equals(r.getUrl().getHost())){
     String path=r.getUrl().getPath();if(path==null||path.equals("/"))path="/index.html";
     if(path.contains(".."))return response("text/plain","Invalid path");
     try {String mime=path.endsWith(".js")?"text/javascript":path.endsWith(".css")?"text/css":path.endsWith(".json")?"application/json":"text/html";return new WebResourceResponse(mime,"UTF-8",getAssets().open(path.substring(1)));}catch(Exception e){return response("text/plain","Not found");}
    }return null;
   }
   @Override public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest r){
    String u=r.getUrl().toString();if(u.startsWith(LOCAL)||sameOrigin(u,server))return false;
    if("http".equals(r.getUrl().getScheme())||"https".equals(r.getUrl().getScheme()))try{startActivity(new Intent(Intent.ACTION_VIEW,r.getUrl()));}catch(Exception ignored){}
    return true;
   }
   @Override public void onReceivedError(WebView v,WebResourceRequest r,WebResourceError e){if(r.isForMainFrame())runOnUiThread(()->{status.setText("连接失败，请检查服务器是否启动、Wi-Fi 和防火墙。可切换离线题库。");});}
  });
  web.setDownloadListener((url,ua,disposition,mime,length)->{
   if(!sameOrigin(url,server)){Toast.makeText(this,"请从当前服务下载",Toast.LENGTH_SHORT).show();return;}
   try{DownloadManager.Request req=new DownloadManager.Request(Uri.parse(url));String name=mime!=null&&mime.contains("pdf")?"fox-certificate.pdf":"fox-answer.js";req.addRequestHeader("Cookie",CookieManager.getInstance().getCookie(url));req.setTitle(name);req.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);req.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS,name);((DownloadManager)getSystemService(DOWNLOAD_SERVICE)).enqueue(req);Toast.makeText(this,"已开始下载",Toast.LENGTH_SHORT).show();}catch(Exception e){Toast.makeText(this,"下载失败，请使用浏览器打开服务",Toast.LENGTH_LONG).show();}
  });
  offline();
 }
 private WebResourceResponse response(String mime,String text){return new WebResourceResponse(mime,"UTF-8",new ByteArrayInputStream(text.getBytes(StandardCharsets.UTF_8)));}
 private boolean sameOrigin(String url,String origin){try{Uri a=Uri.parse(url),b=Uri.parse(origin);return a.getScheme()!=null&&a.getScheme().equals(b.getScheme())&&a.getHost()!=null&&a.getHost().equals(b.getHost())&&a.getPort()==b.getPort();}catch(Exception e){return false;}}
 private void button(LinearLayout row,String text,Runnable action){Button b=new Button(this);b.setText(text);b.setTextSize(12);row.addView(b,new LinearLayout.LayoutParams(0,-2,1));b.setOnClickListener(v->action.run());}
 private void offline(){status.setText("离线模式 · 题库已内置 · 学校/实训功能请连接服务");web.loadUrl(LOCAL);}
 private void settings(){
  EditText address=new EditText(this);address.setSingleLine(true);address.setText(getPreferences(0).getString("server","https://jouxyfwglzx.cn"));address.setInputType(17);
  new AlertDialog.Builder(this).setTitle("连接 fox 后端").setMessage("输入电脑或服务器的地址。局域网需连接同一 Wi-Fi，并启动 python server.py。HTTP 会明文传输账号密码；公网请使用 HTTPS。").setView(address).setPositiveButton("连接",(d,w)->{
   String value=address.getText().toString().trim().replaceAll("/+$","");Uri u=Uri.parse(value);
   if(!("http".equals(u.getScheme())||"https".equals(u.getScheme()))||u.getHost()==null||u.getUserInfo()!=null||u.getQuery()!=null||u.getFragment()!=null||!(u.getPath()==null||u.getPath().isEmpty())){Toast.makeText(this,"请输入 http(s)://主机:端口，不包含路径",Toast.LENGTH_LONG).show();return;}
   server=value;getPreferences(0).edit().putString("server",value).apply();status.setText("在线服务 · "+value);web.loadUrl(value+"/");
  }).setNegativeButton("取消",null).show();
 }
 private void copyScript(){try(InputStream in=getAssets().open("adapter.js")){byte[] bytes=readAll(in);((ClipboardManager)getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("fox 页面助手",new String(bytes,StandardCharsets.UTF_8)));Toast.makeText(this,"完整 fox 脚本已复制，粘贴到用户脚本编辑器使用",Toast.LENGTH_LONG).show();}catch(Exception e){Toast.makeText(this,"复制失败",Toast.LENGTH_SHORT).show();}}
 private byte[] readAll(InputStream in)throws Exception{java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream();byte[] buffer=new byte[8192];int n;while((n=in.read(buffer))!=-1)out.write(buffer,0,n);return out.toByteArray();}
 @Override public void onBackPressed(){if(web.canGoBack())web.goBack();else super.onBackPressed();}
 @Override protected void onDestroy(){web.destroy();super.onDestroy();}
}
