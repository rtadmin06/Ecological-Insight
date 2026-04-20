
function goDetectChanges() {
    this.isNavigator = false
    if (this.$route.path === "/detectchanges") {
        this.$message.success('您已经在该界面了哦')
    } else this.$router.push("detectchanges");
}
function goDetectObjects() {
    this.isNavigator = false;
    if (this.$route.path === "/detectobjects") {
        this.$message.success('您已经在该界面了哦')
    } else this.$router.push("detectobjects");
}
function goSegmentation() {
    this.isNavigator = false;
    if (this.$route.path === "/segmentation") {
        this.$message.success('您已经在该界面了哦')
    } else this.$router.push("segmentation");
}

function goClassification() {
    this.isNavigator = false;
    if (this.$route.path === "/classification") {
        this.$message.success('您已经在该界面了哦')
    } else this.$router.push("classification");
}

function goRestoreImgs() {
    this.isNavigator = false;
    if (this.$route.path === "/restoreimgs") {
        this.$message.success('您已经在该界面了哦')
    } else this.$router.push("restoreimgs");
}

function goOnlineMap(){
    this.isNavigator = false
    if (this.$route.path === "/onlinemap") {
        this.$message.success('您已经在该界面了哦')
    } else this.$router.push("onlinemap");
}
function goHistory() {
    if (this.$route.path === "/history") { this.$message.success('您已经在该界面了哦') }
    else
        this.$router.push({
            name: "history",
        });
}
function goClassification2() {
    this.isNavigator = false;
    if (this.$route.path === "/classification2") {
        this.$message.success('您已经在该界面了哦')
    } else this.$router.push("classification2");
}
function goOnlineMap1() {
    this.isNavigator = false;
    if (this.$route.path === "/onlinemap1") {
        this.$message.success('您已经在该界面了哦')
    } else this.$router.push("onlinemap1");
}
function goHistory1() {
    this.isNavigator = false;
    if (this.$route.path === "/history1") {
        this.$message.success('您已经在该界面了哦')
    } else this.$router.push("history1");
}
export { goDetectChanges, goDetectObjects, goSegmentation, goClassification, goRestoreImgs, goOnlineMap, goHistory, goClassification2, goOnlineMap1, goHistory1 }
