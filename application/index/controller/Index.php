<?php
namespace app\index\controller;
use \think\Controller;
use \think\View;
use \think\Db;
class Index extends \think\Controller
{
	private $tables = array("rank"=>"wx_rank","category"=>"wx_category","gzh"=>"wx_gzh","articles"=>"wx_articles");

    // 获取公众号分类列表
    private function get_cat_list(){
        $sql = "select * from ".$this->tables['category'];
        $cat_list = Db::query($sql);  
        return $cat_list;
    }
    // 查询某个分类下的所有微信号
    private function get_wx_list($cat_id){
        $sql = "select rank,wx_id from ".$this->tables['rank']." where cat_id = ".$cat_id;  
        $wx_list = Db::query($sql);

        // 查询微信号详细信息
        foreach ($wx_list as $key => $val) {
            $wx_id = $val['wx_id'];
            $sql = "select * from ".$this->tables['gzh']." where wx_id=?";          
            $res = Db::query($sql,[$wx_id]);   
            if(count($res)){
                $new_arr = array_merge($wx_list[$key],$res[0]); 
                $wx_list[$key] = $new_arr;   
            }               
        }   
        return $wx_list;     
    }

    //获取微信公众号文章列表
    private function get_article_list($wx_id,$page=1,$page_size=20){
        $article_list = array();
        if(isset($wx_id)){
            $start = ($page-1)*$page_size;
            $sql = "select * from ".$this->tables['articles']." where wx_id='$wx_id' limit $start,$page_size";
            print($sql);
            $article_list = Db::query($sql);
        }
        return $article_list;
    }

    public function index()
    {
    	$cat_list = $this->get_cat_list();
    	$cat_id = 1;
        $wx_list = $this->get_wx_list($cat_id);
        // 批量赋值
        $this->assign([
            'name'  => 'ThinkPHP',
            'cat_list' => $cat_list,
            'wx_list'=> $wx_list
        ]);
        // 模板输出
        return $this->fetch('index');
    }

    public function getCategory($id){
        $wx_list = array();
        if(isset($id)){
            $wx_list = $this->get_wx_list($id);
        }  
        return  json_encode(array('data' => $wx_list));   
    }

    public function getArticleList($id,$page=1){
       return $this->get_article_list($id);
    }
}
