
<template>
  <div>
    <div class="hint">
      灾情信息查询：<i
        style="margin-left: 8px; font-size: 20px"
       
      />
    </div>
    <el-table
      
      
    >
    
      <el-table-column type="selection" />
      <el-table-column label="日期">
        
        
      </el-table-column>
      
     
    </el-table>

    <el-table
      ref="multipleTable"
      
      
    >
      <el-table-column type="selection" />
      <el-table-column label="监测区域">
        
      </el-table-column>
    </el-table>
    <el-table
      ref="multipleTable"
      
     
    >
      <el-table-column type="selection" />
      <el-table-column label="变化程度">
       
      </el-table-column>
    </el-table>

    <el-table
      ref="multipleTable"
     
     
    >
      <el-table-column type="selection" />
      <el-table-column label="整体区域损伤程度">
        
      </el-table-column>
    </el-table>

    <el-table
      ref="multipleTable"
      
    >
      <el-table-column type="selection" />
      <el-table-column label="局部区域损伤程度">
       
      </el-table-column>
    </el-table>

  
    <el-row justify="center">
        <el-button
          type="primary"
          class="btn-animate btn-animate__shiny"
          
        >
          查询
        </el-button>
      </el-row>
  </div>
</template>



